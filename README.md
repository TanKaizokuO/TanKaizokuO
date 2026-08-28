<h2 align="left">Tanishq Bhattacharjee</h2>

<p align="left">
I build production-shaped LLM systems and the backends they run on — agent runtimes, retrieval pipelines with real evaluation harnesses, and APIs that hold up under load.<br>
Final-year CSE @ IIIT Naya Raipur. Open to <b>AI Engineer</b> and <b>Full-Stack / Backend SWE</b> roles — India or remote.
</p>

###

### What I work with

| | |
|---|---|
| **Languages** | Python, TypeScript, Rust, Go, C, SQL |
| **Backend** | FastAPI, Node/Express, PostgreSQL, REST, GraphQL, SSE/WebSockets, Docker |
| **Frontend** | React, Next.js, TypeScript, Tailwind |
| **AI / ML** | PyTorch, Hugging Face, LangGraph, LangChain, MCP, RAG, LLM evaluation |
| **Practices** | OOP, concurrency, CI/CD, testing, observability |

###

<p align="left">
  <a href="https://www.linkedin.com/in/tanishq-bhattacharjee-44ba7b325/">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" height="28" alt="LinkedIn" />
  </a>
  <a href="mailto:tanishqbhattacharjee22@gmail.com">
    <img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" height="28" alt="Email" />
  </a>
</p>

# 💻 Featured Projects

## 🗄️ [Sibyl-SQL](https://github.com/TanKaizokuO/Sibyl_SQL) — Conversational Postgres with unforgeable access control

A natural-language database agent where security is enforced by the database kernel, not the app layer. A LangChain **ReAct** agent plans multi-step queries while **PostgreSQL Row-Level Security** makes privilege escalation impossible by design — the agent is never trusted. Reasoning traces stream to the browser over SSE, and results auto-render as charts, tables, or choropleth maps.

**Tech:** `Python` `PostgreSQL RLS` `LangChain ReAct` `React` `SSE` `Docker Compose`

---

## 🧬 [Biomedical QA](https://github.com/TanKaizokuO/BioMedical_QA) — Evidence-grounded answers, measured for faithfulness

A biomedical QA system that answers as **atomic claims, each attributed to the passage that supports it**, with a faithfulness verifier on top. Built as a real evaluation harness first: separate scorers for citation quality, retrieval, calibration, abstention, annotator agreement, granularity, and cost — with 30+ architecture decision records and 31 test modules recording why each choice was made.

**Tech:** `Python` `vLLM` `Retrieval Cascade` `Eval Harness` `ADRs` `uv`

---

## 🤖 [Nakama-kun](https://github.com/TanKaizokuO/nakama_kun) — Verification-driven autonomous coding agent

A terminal-first coding agent built on **LangGraph** that refuses to claim success it cannot prove. Every file write and command is cross-checked against the workspace, `pytest` logs are parsed before the agent proceeds, and an immutable evidence store grounds the final report to eliminate hallucinated results. Long-term memory (SQLite + ChromaDB) recalls past failures to steer planning. 59 test modules.

**Tech:** `Python` `LangGraph` `MCP` `ChromaDB` `Typer` `RAG`

---

## 🌐 [Backend, from a socket to a deploy](https://github.com/TanKaizokuO/backend-curriculum) — Sixteen lessons, one real API

A backend curriculum that starts at `socket.accept()` and a hand-written HTTP response, and ends at TLS, reverse proxies, and the rules a browser enforces — passing through migrations, indexing, concurrency, caching, observability, and scaling on the way. Every number in it is real output from a reproducible script: a `text_pattern_ops` B-tree taking a prefix search over 200k rows from **11.810 ms → 0.128 ms**, and N+1 going from 7× to **51× slower** than a join once 1 ms of network latency is added. Core track in Python, with a parallel Express/TypeScript track.

**Tech:** `FastAPI` `PostgreSQL` `psycopg3` `Docker` `TypeScript` `Express`

---

## 🔌 [mcpctl](https://github.com/TanKaizokuO/MCP_2) — Reading the Model Context Protocol spec closely

A CLI and two reference servers built to compare the **MCP `2025-11-25`** specification against the upcoming **`2026-07-28`** revision. Implements both sides of the change: the legacy stateful handshake with session affinity, and the new stateless core where every request is self-contained via `_meta` and `Mcp-Method` header routing — plus the OAuth flow. `--verbose` prints raw protocol frames.

**Tech:** `Python` `FastAPI` `MCP` `OAuth` `Protocol Design`

---

## 🔬 [Research Assistant](https://github.com/TanKaizokuO/research-assistant) — Multi-source literature agent grounded in page citations

A research assistant that ingests user-uploaded PDFs into a local vector store with **section-aware chunking**, then answers over hybrid dense + sparse retrieval (BM25 + cross-encoder reranking) fused via Reciprocal Rank Fusion. A **LangGraph** agent dynamically selects tools to supplement local documents with live arXiv, Semantic Scholar, and web search, streaming tokens and tool calls to the UI over SSE. Every citation traces back to an exact section and page range.

**Tech:** `Python` `LangGraph` `FastAPI` `ChromaDB` `React` `SSE`

---

## ⚙️ [Nakama](https://github.com/TanKaizokuO/nakama) — Agent runtime in Rust

The same problem as Nakama-kun, solved a second time in a systems language to find out what the Python version was hiding. Multi-provider SSE streaming on **tokio**, sandboxed tool dispatch with path-scope validation on every filesystem call, an MCP bridge, and automatic transcript compaction when the context window fills.

**Tech:** `Rust` `tokio` `SSE` `MCP` `async`

---

## 🧮 [C-Learn](https://github.com/TanKaizokuO/C-Learn) — A machine learning library in C

Written to understand what the frameworks abstract away. A hand-rolled matrix type, dense layers, activations, loss functions, optimizers, and backpropagation — all from scratch in C with no external dependencies. The test suite includes **numerical gradient checking** against the analytic backward pass, and an architecture decision record explains why the sigmoid + binary-cross-entropy gradient is fused. Ships end-to-end examples: linear regression, logistic regression, and a neural network trained on the Titanic dataset.

**Tech:** `C` `Makefile` `Linear Algebra` `Backpropagation`

---
