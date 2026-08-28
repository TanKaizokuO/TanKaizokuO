#!/usr/bin/env python3
"""Render a neofetch-style GitHub profile card (dark_mode.svg / light_mode.svg).

Static lines come from profile.json, the GitHub Stats block is fetched live from
the GraphQL API. Line-of-code totals are walked per repository and cached in
loc_cache.json so daily runs stay cheap.

    GITHUB_TOKEN=<pat> USER_NAME=<login> python3 generate.py
    python3 generate.py --demo        # no network, placeholder numbers
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = "https://api.github.com/graphql"
CACHE = ROOT / "loc_cache.json"

# ---------------------------------------------------------------- layout ------

DOT_PITCH_MIN, DOT_PITCH_MAX = 5.0, 8.0  # px between braille dot centres
DOT_FILL = 0.92  # dot size as a fraction of the pitch
ART_SCALE = 0.86  # art height as a fraction of the info column height
INFO_FS, INFO_LH = 15.0, 21.5
PAD = 36.0
GAP = 38.0
COLS = 60  # character width of the info column
FONTS = (
    "'DejaVu Sans Mono','Menlo','Cascadia Mono','Liberation Mono',"
    "'Consolas',monospace"
)

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "art": "#f2c14e",
        "art2": "#e5484d",
        "head": "#ff7b72",
        "label": "#f2c14e",
        "value": "#e6edf3",
        "dim": "#7d8590",
        "add": "#3fb950",
        "del": "#f85149",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "art": "#bf8700",
        "art2": "#cf222e",
        "head": "#cf222e",
        "label": "#9a6700",
        "value": "#1f2328",
        "dim": "#6e7781",
        "add": "#1a7f37",
        "del": "#cf222e",
    },
}

# ------------------------------------------------------------------ api -------


def graphql(query: str, variables: dict, token: str) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-card",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:  # surface GitHub's message, not a traceback
        raise SystemExit(f"GitHub API {exc.code}: {exc.read().decode()[:400]}") from exc
    if "errors" in payload:
        raise SystemExit(f"GitHub API errors: {payload['errors']}")
    return payload["data"]


USER_Q = """
query ($login: String!) {
  user(login: $login) {
    id
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER) { totalCount }
    repositoriesContributedTo(
      includeUserRepositories: false
      contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY, PULL_REQUEST_REVIEW]
    ) { totalCount }
  }
}
"""

REPOS_Q = """
query ($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(
      first: 100
      after: $cursor
      isFork: false
      ownerAffiliations: OWNER
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        nameWithOwner
        stargazerCount
        defaultBranchRef { target { ... on Commit { oid } } }
      }
    }
  }
}
"""

COMMITS_Q = """
query ($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor, author: {id: $id}) {
            totalCount
            pageInfo { hasNextPage endCursor }
            nodes { additions deletions }
          }
        }
      }
    }
  }
}
"""

YEAR_Q = """
query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      restrictedContributionsCount
    }
  }
}
"""


def lifetime_commits(login: str, created: datetime, token: str) -> int:
    """contributionsCollection caps at one year, so sum year by year."""
    total = 0
    now = datetime.now(timezone.utc)
    start = created
    while start < now:
        end = min(start.replace(year=start.year + 1), now)
        data = graphql(
            YEAR_Q,
            {"login": login, "from": start.isoformat(), "to": end.isoformat()},
            token,
        )
        c = data["user"]["contributionsCollection"]
        total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
        start = end
    return total


def repo_loc(name_with_owner: str, user_id: str, token: str) -> tuple[int, int, int]:
    owner, name = name_with_owner.split("/", 1)
    adds = dels = commits = 0
    cursor = None
    while True:
        data = graphql(
            COMMITS_Q,
            {"owner": owner, "name": name, "id": user_id, "cursor": cursor},
            token,
        )
        branch = data["repository"]["defaultBranchRef"]
        if not branch:
            break
        hist = branch["target"]["history"]
        commits = hist["totalCount"]
        for node in hist["nodes"]:
            adds += node["additions"]
            dels += node["deletions"]
        if not hist["pageInfo"]["hasNextPage"]:
            break
        cursor = hist["pageInfo"]["endCursor"]
    return adds, dels, commits


def fetch_stats(login: str, token: str) -> dict:
    user = graphql(USER_Q, {"login": login}, token)["user"]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))

    stars = 0
    repos: list[tuple[str, str]] = []
    cursor = None
    while True:
        page = graphql(REPOS_Q, {"login": login, "cursor": cursor}, token)["user"][
            "repositories"
        ]
        for node in page["nodes"]:
            stars += node["stargazerCount"]
            branch = node["defaultBranchRef"]
            if branch:
                repos.append((node["nameWithOwner"], branch["target"]["oid"]))
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    fresh: dict[str, dict] = {}
    adds = dels = 0
    for name, head in repos:
        hit = cache.get(name)
        if not hit or hit.get("oid") != head:
            a, d, _ = repo_loc(name, user["id"], token)
            hit = {"oid": head, "additions": a, "deletions": d}
        fresh[name] = hit
        adds += hit["additions"]
        dels += hit["deletions"]
    CACHE.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n")

    return {
        "created": created,
        "repos": user["repositories"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "stars": stars,
        "commits": lifetime_commits(login, created, token),
        "additions": adds,
        "deletions": dels,
    }


def demo_stats() -> dict:
    return {
        "created": datetime(2019, 4, 17, tzinfo=timezone.utc),
        "repos": 95,
        "contributed": 133,
        "followers": 196,
        "stars": 342,
        "commits": 2116,
        "additions": 523178,
        "deletions": 76902,
    }


# ----------------------------------------------------------------- text -------


def age(created: datetime) -> str:
    now = datetime.now(timezone.utc)
    years = now.year - created.year
    months = now.month - created.month
    days = now.day - created.day
    if days < 0:
        months -= 1
        prev = (now.month - 1) or 12
        year = now.year if now.month > 1 else now.year - 1
        days += (datetime(year, prev % 12 + 1, 1) - datetime(year, prev, 1)).days
    if months < 0:
        years -= 1
        months += 12
    plural = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")
    return ", ".join(
        [plural(years, "year"), plural(months, "month"), plural(days, "day")]
    )


def build_lines(profile: dict, stats: dict) -> list[dict]:
    """Each line is {kind, segs}: segs are (text, color-key) in char order."""
    lines: list[dict] = []

    def header(text: str, color: str) -> None:
        pad = COLS - len(text) - 2
        lines.append(
            {
                "segs": [
                    (text + " ", color),
                    ("-" * max(pad, 1), "dim"),
                    ("-", "dim"),
                ]
            }
        )

    def row(label: str, value_segs: list[tuple[str, str]]) -> None:
        plain = sum(len(t) for t, _ in value_segs)
        dots = COLS - 2 - len(label) - 1 - 1 - 1 - plain
        lines.append(
            {
                "segs": [
                    (". ", "dim"),
                    (f"{label}:", "label"),
                    (" " + "." * max(dots, 1) + " ", "dim"),
                    *value_segs,
                ]
            }
        )

    header(profile["user_line"], "head")
    lines.append({"segs": []})

    for section in profile["sections"]:
        if section.get("title"):
            header(f"- {section['title']}", "value")
        for label, value in section["rows"]:
            row(label, [(value, "value")])
        lines.append({"segs": []})

    header("- GitHub Stats", "value")
    row("Uptime", [(age(stats["created"]), "value")])
    row(
        "Repos",
        [
            (f"{stats['repos']:,} ", "value"),
            (f"{{Contributed: {stats['contributed']:,}}}", "dim"),
        ],
    )
    row("Stars", [(f"{stars_fmt(stats)}", "value")])
    row("Followers", [(f"{stats['followers']:,}", "value")])
    row("Commits", [(f"{stats['commits']:,}", "value")])
    loc = stats["additions"] - stats["deletions"]
    row(
        "Lines of Code",
        [
            (f"{loc:,} ( ", "value"),
            (f"{stats['additions']:,}++", "add"),
            (", ", "value"),
            (f"{stats['deletions']:,}--", "del"),
            (" )", "value"),
        ],
    )
    while lines and not lines[-1]["segs"]:
        lines.pop()
    return lines


def stars_fmt(stats: dict) -> str:
    return f"{stats['stars']:,}"


# ------------------------------------------------------------------ svg -------


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# Braille bit -> (dot column, dot row) inside a 2x4 cell.
DOT_MAP = (
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 0),
    (1, 1),
    (1, 2),
    (0, 3),
    (1, 3),
)


def art_path(art: list[str], pitch: float) -> str:
    """Decode braille cells into one filled path so no font is involved."""
    size = pitch * DOT_FILL
    inset = (pitch - size) / 2
    parts: list[str] = []
    for row_i, row in enumerate(art):
        for col_i, char in enumerate(row):
            bits = ord(char) - 0x2800
            if not 0 <= bits <= 0xFF:
                continue
            for bit, (dx, dy) in enumerate(DOT_MAP):
                if not bits >> bit & 1:
                    continue
                x = (col_i * 2 + dx) * pitch + inset
                y = (row_i * 4 + dy) * pitch + inset
                parts.append(f"M{x:.1f} {y:.1f}h{size:.1f}v{size:.1f}h-{size:.1f}z")
    return "".join(parts)


def render(art: list[str], lines: list[dict], theme: dict) -> str:
    info_w = COLS * INFO_FS * 0.6
    info_h = len(lines) * INFO_LH
    dot_rows, dot_cols = len(art) * 4, max(len(row) for row in art) * 2
    # size the art to most of the info column's height, within sane bounds
    pitch = min(max(info_h * ART_SCALE / dot_rows, DOT_PITCH_MIN), DOT_PITCH_MAX)
    art_w, art_h = dot_cols * pitch, dot_rows * pitch
    content_h = max(art_h, info_h)
    width = round(PAD * 2 + art_w + GAP + info_w)
    height = round(PAD * 2 + content_h)

    out: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="GitHub profile stats">',
        "<style>"
        f"text{{font-family:{FONTS};white-space:pre;dominant-baseline:middle}}"
        f".info{{font-size:{INFO_FS}px}}"
        "</style>",
        f'<defs><linearGradient id="art" x1="0" y1="0" x2="0.35" y2="1">'
        f'<stop offset="0" stop-color="{theme["art"]}"/>'
        f'<stop offset="1" stop-color="{theme["art2"]}"/></linearGradient></defs>',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
    ]

    art_top = PAD + (content_h - art_h) / 2
    out.append(
        f'<g transform="translate({PAD:.1f} {art_top:.1f})">'
        f'<path fill="url(#art)" d="{art_path(art, pitch)}"/></g>'
    )

    info_x = PAD + art_w + GAP
    info_top = PAD + (content_h - info_h) / 2
    for i, line in enumerate(lines):
        if not line["segs"]:
            continue
        y = info_top + i * INFO_LH + INFO_LH / 2
        spans = "".join(
            f'<tspan fill="{theme[color]}">{esc(text)}</tspan>'
            for text, color in line["segs"]
        )
        out.append(f'<text class="info" x="{info_x:.1f}" y="{y:.1f}">{spans}</text>')

    out.append("</svg>")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ main ------


def main() -> None:
    demo = "--demo" in sys.argv
    profile = json.loads((ROOT / "profile.json").read_text())
    art = (ROOT / profile.get("art_file", "luffy.txt")).read_text().rstrip("\n").split("\n")
    width = max(len(row) for row in art)
    art = [row.ljust(width) for row in art]

    if demo:
        stats = demo_stats()
    else:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN")
        login = os.environ.get("USER_NAME")
        if not token or not login:
            raise SystemExit("set GITHUB_TOKEN and USER_NAME (or pass --demo)")
        stats = fetch_stats(login, token)
        profile["user_line"] = profile.get("user_line") or f"{login}@github"

    lines = build_lines(profile, stats)
    for name, theme in THEMES.items():
        (ROOT / f"{name}_mode.svg").write_text(render(art, lines, theme))
        print(f"wrote {name}_mode.svg")


if __name__ == "__main__":
    main()
