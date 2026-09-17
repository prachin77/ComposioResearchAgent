# Composio 100-App AI Integration Research

Automated research agent that analyzes 100 applications across 10 categories for API integration readiness — authentication patterns, API surfaces, access models, MCP servers, and buildability for AI agent toolkits.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Google Gemini API key (free): [Get one here](https://aistudio.google.com/apikey)

### 2. Setup
```bash
git clone <this-repo>
cd composio-100-app-research
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run the Research Pipeline
```bash
# Full pipeline: research → verify → analyze → save dataset
py scripts/run_research.py

# Force re-research all apps (ignores cache)
py scripts/run_research.py --force
```

### 4. Generate the HTML Report
```bash
py scripts/generate_html.py
# Opens output/index.html
```

### 5. Deploy to Vercel
```bash
cd output
npx vercel --prod
```

## 📁 Project Structure

```
├── config.py              # Central configuration
├── models.py              # Pydantic data models
├── data/
│   ├── apps.json          # Input: 100 apps
│   ├── results/           # Per-app research results (JSON)
│   ├── cache/             # Cached web pages
│   ├── analysis_results.json
│   └── verification_results.json
├── agent/
│   ├── llm.py             # Gemini LLM client
│   ├── search.py          # DuckDuckGo web search
│   ├── scraper.py         # URL content extraction
│   ├── researcher.py      # Per-app research pipeline
│   ├── orchestrator.py    # Main pipeline runner
│   └── verifier.py        # 3-layer verification
├── analysis/
│   └── patterns.py        # Pattern extraction
├── scripts/
│   ├── run_research.py    # Entry point: full pipeline
│   └── generate_html.py   # Entry point: HTML generation
└── output/
    ├── index.html          # THE deliverable
    └── data.json           # Machine-readable dataset
```

## 🔬 How It Works

For each of the 100 apps, the agent:

1. **Searches** for API documentation and authentication info (DuckDuckGo, 3 queries/app)
2. **Fetches** and extracts text from top documentation pages (httpx + trafilatura)
3. **Searches** for MCP servers on GitHub/npm
4. **Extracts** structured data via LLM (Google Gemini Flash, 1 call/app)
5. **Scores** confidence based on evidence quality

Then runs a 3-layer verification:
- **Layer 1**: Automated cross-validation (fresh search vs original claims)
- **Layer 2**: Consistency checks (logical contradiction detection)
- **Layer 3**: Human spot-check protocol (20-app sample)

## 📊 What Gets Researched

For each app: category, description, auth methods (OAuth2/API key/token/basic), access model (self-serve/paid/gated), API surface (REST/GraphQL, breadth), webhooks, SDKs, MCP servers (official/community), buildability verdict, primary blockers, confidence level, and evidence URLs.

## ⏱️ Runtime

- **Full pipeline**: ~25-35 minutes (within Gemini free tier limits)
- **HTML generation only**: < 5 seconds (from cached results)
- **Resume-safe**: Caches each app result to disk; restart continues from where it stopped

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Google Gemini Flash (free tier) |
| Search | DuckDuckGo (no API key needed) |
| Scraping | httpx + trafilatura |
| Data | Pydantic models + JSON |
| Frontend | Single-file HTML + Chart.js |
| Deployment | Vercel (free tier) |
