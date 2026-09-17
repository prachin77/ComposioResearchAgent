# Composio 100-App AI Integration Research

Automated research agent that analyzes 100 applications across 10 categories for API integration readiness — authentication patterns, API surfaces, access models, MCP servers, and buildability for AI agent toolkits.

Built with **Composio SDK**, **Google Gemini**, and **Tavily / DuckDuckGo search**.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Google Gemini API key (free): [Get one at AI Studio](https://aistudio.google.com/apikey)
- *(Optional)* Composio API key: [Get one at app.composio.dev](https://app.composio.dev)

### 2. Setup
```bash
git clone <this-repo>
cd ComposioResearchAgent
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to configure your API keys:
```env
# Required: Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Composio SDK API Key (auto-enables Composio tool execution)
COMPOSIO_API_KEY=your_composio_api_key_here
```

### 3. Run the Research Pipeline
```bash
# Full pipeline: research → verify → analyze → generate HTML deliverable
py scripts/run_research.py

# Force re-research all apps (bypasses disk cache)
py scripts/run_research.py --force
```

### 4. View the Interactive Deliverable
Double-click `output/index.html` or open it in your browser:
```powershell
Start-Process output/index.html
```

*(Optional)* If you only want to re-render the HTML from existing data:
```bash
py scripts/generate_html.py
```

### 5. Deploy to Vercel
```bash
cd output
npx vercel --prod
```

---

## 📁 Project Structure

```
├── config.py              # Central configuration (Gemini & Composio settings)
├── models.py              # Strict Pydantic data schemas
├── data/
│   ├── apps.json          # Input list: 100 apps across 10 categories
│   ├── results/           # Per-app research results (cached JSON files)
│   ├── cache/             # Scraped documentation cache
│   ├── analysis_results.json
│   └── verification_results.json
├── agent/
│   ├── llm.py             # Gemini client with rate limiting & retries
│   ├── search.py          # Search: Composio SDK (Tavily) + DuckDuckGo fallback
│   ├── scraper.py         # URL content extraction (httpx + trafilatura)
│   ├── researcher.py      # Per-app research & structured data extraction
│   ├── orchestrator.py    # Pipeline runner with progress tracking & checkpointing
│   └── verifier.py        # 3-layer verification & 20-app spot-check protocol
├── analysis/
│   └── patterns.py        # Cross-category analytics & blocker aggregation
├── scripts/
│   ├── test_pipeline.py   # Quick 2-app validation test
│   ├── run_research.py    # Main entry point (full end-to-end pipeline)
│   └── generate_html.py   # Standalone HTML report generator
└── output/
    ├── index.html         # Final interactive self-contained case study dashboard
    └── data.json          # Complete machine-readable dataset (100 apps + analysis)
```

---

## 🔬 How It Works

For each of the 100 apps, the research agent:

1. **Searches Docs**: Executes targeted search queries via Composio SDK / Tavily (or DuckDuckGo fallback).
2. **Scrapes Content**: Fetches and extracts clean markdown/text from developer documentation (`httpx` + `trafilatura`).
3. **Searches MCP Servers**: Discovers official and community Model Context Protocol (MCP) servers on GitHub/npm.
4. **Structured LLM Extraction**: Extracts verified technical facts via Gemini (`gemini-3-flash-preview`).
5. **Confidence & Evidence Scoring**: Generates explicit confidence ratings (`high`, `medium`, `low`) backed by source citations.

### 3-Layer Verification Protocol
- **Layer 1 (Automated Cross-Validation)**: Fresh automated search to verify key claims against secondary sources.
- **Layer 2 (Consistency Checks)**: Rule-based contradiction detection (e.g., OAuth scopes vs auth methods, free tier vs access model).
- **Layer 3 (Human Spot-Check)**: Pre-configured 20-app balanced sample (2 per category, major & niche mix) with field-level accuracy scoring.

---

## 📊 What Gets Captured

- **Category & Description**: 1-line summary of what the app does.
- **Authentication**: `OAuth2`, `API key`, `Basic`, `Token`, or `Other` (with primary auth designated).
- **Access & Pricing Model**: Self-serve free/trial vs paid plan vs partner-gated approval.
- **API Surface**: Protocol (`REST`, `GraphQL`, `gRPC`), breadth (`broad`, `narrow`, `none`), docs URL, webhooks, official SDKs.
- **MCP Ecosystem**: Official MCP server, community MCP server, or none.
- **AI Agent Buildability**: Verdict (`ready`, `needs_partnership`, `blocked`, `unclear`), blocker type, and blocker explanation.
- **Confidence & Evidence**: High/medium/low score with direct documentation URLs.

---

## ⏱️ Runtime & Resilience

- **Full Pipeline (100 apps)**: ~25–35 minutes (respects Gemini free-tier rate limits).
- **Resume-Safe**: Automatically caches every researched app in `data/results/{id}.json`. If interrupted, restarting resumes from where it left off.
- **HTML Generation**: < 2 seconds from cached results.

---

## 🛠️ Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Agent / Tools** | **Composio SDK (`composio`)** | Direct tool execution for Tavily search & developer MCP workflows |
| **LLM** | **Google Gemini (`gemini-3-flash-preview`)** | Fast, high accuracy, structured JSON schema output on free tier |
| **Search Fallback** | **DuckDuckGo (`ddgs`)** | Zero-config fallback ensuring 100% pipeline reliability |
| **Scraping** | **`httpx` + `trafilatura`** | High-speed async extraction of main documentation text |
| **Data Schemas** | **Pydantic v2** | Strict typing, schema enforcement, and JSON serialization |
| **Visualization** | **Chart.js + Vanilla CSS** | Single-file interactive HTML dashboard with dark mode & export tools |
| **Deployment** | **Vercel** | Free zero-config static hosting |
