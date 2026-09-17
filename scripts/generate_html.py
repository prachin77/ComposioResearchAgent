"""
HTML Case Study Generator — produces the final deliverable.
Generates a stunning, self-contained HTML page from the research data.
Usage: python scripts/generate_html.py
"""
import sys
import os
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_dataset():
    """Load the combined dataset from output/data.json."""
    dataset_path = config.OUTPUT_DIR / "data.json"
    if not dataset_path.exists():
        print(f"ERROR: {dataset_path} not found. Run the research pipeline first:")
        print(f"  python scripts/run_research.py")
        sys.exit(1)
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_html(dataset: dict) -> str:
    """Generate the complete HTML page."""
    results = dataset["results"]
    analysis = dataset["analysis"]
    verification = dataset["verification"]

    # Pre-compute some stats for the hero section
    total_apps = len(results)
    self_serve_count = sum(1 for r in results if r.get("self_serve_signup"))
    buildable_count = sum(1 for r in results if r.get("buildability") in ("ready", "buildable"))
    oauth_count = sum(1 for r in results if r.get("oauth2_available"))
    has_api_count = sum(1 for r in results if r.get("has_public_api"))
    any_mcp = analysis.get("mcp_stats", {}).get("any_mcp", 0)

    # Categories list
    categories = sorted(set(r.get("category", "") for r in results))

    # JSON-encode the data for embedding
    results_json = json.dumps(results, default=str)
    analysis_json = json.dumps(analysis, default=str)
    verification_json = json.dumps(verification, default=str)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>100-App AI Integration Landscape | Composio Research</title>
    <meta name="description" content="Automated research across 100 apps: auth patterns, API surfaces, MCP servers, and integration readiness for AI agent toolkits.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        :root {{
            --bg-primary: #06060f;
            --bg-secondary: #0d0d1a;
            --bg-card: rgba(15, 15, 35, 0.7);
            --bg-card-hover: rgba(25, 25, 55, 0.8);
            --border: rgba(99, 102, 241, 0.15);
            --border-hover: rgba(99, 102, 241, 0.35);
            --text-primary: #f0f0ff;
            --text-secondary: #a0a0c0;
            --text-muted: #6b6b8d;
            --accent-1: #6366f1;
            --accent-2: #8b5cf6;
            --accent-3: #a78bfa;
            --green: #34d399;
            --yellow: #fbbf24;
            --red: #f87171;
            --blue: #60a5fa;
            --orange: #fb923c;
            --gradient-accent: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
            --gradient-hero: linear-gradient(135deg, #06060f 0%, #0d0d2a 50%, #1a1040 100%);
            --glass: rgba(255, 255, 255, 0.03);
            --glass-border: rgba(255, 255, 255, 0.06);
            --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            --radius: 16px;
            --radius-sm: 8px;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
        }}

        /* --- Animated background --- */
        .bg-grid {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image:
                radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.04) 0%, transparent 50%),
                radial-gradient(circle at 50% 80%, rgba(167, 139, 250, 0.03) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}

        .container {{ max-width: 1400px; margin: 0 auto; padding: 0 32px; position: relative; z-index: 1; }}

        /* --- HERO --- */
        .hero {{
            min-height: 70vh;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            text-align: center; padding: 80px 20px;
            background: var(--gradient-hero);
            position: relative;
        }}
        .hero::after {{
            content: '';
            position: absolute; bottom: 0; left: 0; right: 0; height: 200px;
            background: linear-gradient(to bottom, transparent, var(--bg-primary));
        }}
        .hero-badge {{
            display: inline-flex; align-items: center; gap: 8px;
            background: var(--glass); border: 1px solid var(--glass-border);
            border-radius: 100px; padding: 8px 20px;
            font-size: 0.85rem; color: var(--accent-3);
            margin-bottom: 24px; backdrop-filter: blur(10px);
        }}
        .hero h1 {{
            font-size: clamp(2.5rem, 6vw, 4.5rem);
            font-weight: 900; letter-spacing: -0.03em;
            background: var(--gradient-accent);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text; margin-bottom: 20px;
            line-height: 1.1;
        }}
        .hero-sub {{
            font-size: 1.25rem; color: var(--text-secondary);
            max-width: 700px; margin-bottom: 48px;
        }}
        .hero-stats {{
            display: flex; gap: 40px; flex-wrap: wrap; justify-content: center;
            position: relative; z-index: 2;
        }}
        .hero-stat {{
            text-align: center;
        }}
        .hero-stat .number {{
            font-size: 2.5rem; font-weight: 800;
            background: var(--gradient-accent);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .hero-stat .label {{
            font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;
            letter-spacing: 0.1em; margin-top: 4px;
        }}

        /* --- SECTIONS --- */
        section {{ padding: 80px 0; }}
        .section-header {{
            text-align: center; margin-bottom: 48px;
        }}
        .section-header h2 {{
            font-size: 2rem; font-weight: 800; margin-bottom: 12px;
            letter-spacing: -0.02em;
        }}
        .section-header p {{
            color: var(--text-secondary); font-size: 1.05rem; max-width: 600px; margin: 0 auto;
        }}

        /* --- GLASS CARDS --- */
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 32px;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
        }}
        .card:hover {{
            border-color: var(--border-hover);
            background: var(--bg-card-hover);
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }}

        /* --- KEY FINDINGS GRID --- */
        .findings-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
        }}
        .finding-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 28px;
            backdrop-filter: blur(20px);
            transition: all 0.3s ease;
        }}
        .finding-card:hover {{
            border-color: var(--border-hover);
            transform: translateY(-3px);
            box-shadow: var(--shadow);
        }}
        .finding-card .icon {{ font-size: 2rem; margin-bottom: 12px; }}
        .finding-card .stat {{
            font-size: 2rem; font-weight: 800; margin-bottom: 4px;
            color: var(--accent-3);
        }}
        .finding-card .desc {{
            color: var(--text-secondary); font-size: 0.9rem; line-height: 1.5;
        }}

        /* --- CHARTS --- */
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
        }}
        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 28px;
            backdrop-filter: blur(20px);
        }}
        .chart-card h3 {{
            font-size: 1.1rem; font-weight: 600; margin-bottom: 20px;
            color: var(--text-primary);
        }}
        .chart-container {{
            position: relative;
            height: 300px;
        }}

        /* --- DATA TABLE --- */
        .table-controls {{
            display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; align-items: center;
        }}
        .search-input {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: var(--radius-sm); padding: 10px 16px;
            color: var(--text-primary); font-size: 0.9rem; min-width: 250px;
            outline: none; font-family: inherit;
        }}
        .search-input:focus {{ border-color: var(--accent-1); }}
        .filter-btn {{
            background: var(--glass); border: 1px solid var(--border);
            border-radius: var(--radius-sm); padding: 8px 16px;
            color: var(--text-secondary); font-size: 0.8rem; cursor: pointer;
            transition: all 0.2s; font-family: inherit;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: var(--accent-1); color: white; border-color: var(--accent-1);
        }}

        .data-table {{
            width: 100%; border-collapse: collapse; font-size: 0.85rem;
        }}
        .data-table thead {{
            position: sticky; top: 0; z-index: 10;
        }}
        .data-table th {{
            background: var(--bg-secondary);
            border-bottom: 2px solid var(--border);
            padding: 14px 12px; text-align: left;
            font-weight: 600; color: var(--text-secondary);
            text-transform: uppercase; font-size: 0.75rem;
            letter-spacing: 0.05em; cursor: pointer;
            user-select: none;
        }}
        .data-table th:hover {{ color: var(--accent-3); }}
        .data-table td {{
            padding: 12px; border-bottom: 1px solid var(--glass-border);
            vertical-align: middle;
        }}
        .data-table tr:hover td {{
            background: rgba(99, 102, 241, 0.05);
        }}
        .data-table .app-name {{
            font-weight: 600; color: var(--text-primary);
        }}
        .data-table .cat-badge {{
            display: inline-block; padding: 3px 10px; border-radius: 100px;
            font-size: 0.7rem; font-weight: 500;
            background: var(--glass); border: 1px solid var(--glass-border);
            color: var(--text-secondary); white-space: nowrap;
        }}

        /* Badges */
        .badge {{
            display: inline-block; padding: 3px 10px; border-radius: 100px;
            font-size: 0.7rem; font-weight: 600; white-space: nowrap;
        }}
        .badge-ready {{ background: rgba(52, 211, 153, 0.15); color: var(--green); border: 1px solid rgba(52, 211, 153, 0.3); }}
        .badge-buildable {{ background: rgba(96, 165, 250, 0.15); color: var(--blue); border: 1px solid rgba(96, 165, 250, 0.3); }}
        .badge-needs-setup {{ background: rgba(251, 191, 36, 0.15); color: var(--yellow); border: 1px solid rgba(251, 191, 36, 0.3); }}
        .badge-gated {{ background: rgba(251, 146, 60, 0.15); color: var(--orange); border: 1px solid rgba(251, 146, 60, 0.3); }}
        .badge-blocked {{ background: rgba(248, 113, 113, 0.15); color: var(--red); border: 1px solid rgba(248, 113, 113, 0.3); }}
        .badge-unknown {{ background: var(--glass); color: var(--text-muted); border: 1px solid var(--glass-border); }}

        .badge-high {{ background: rgba(52, 211, 153, 0.15); color: var(--green); border: 1px solid rgba(52, 211, 153, 0.3); }}
        .badge-medium {{ background: rgba(251, 191, 36, 0.15); color: var(--yellow); border: 1px solid rgba(251, 191, 36, 0.3); }}
        .badge-low {{ background: rgba(248, 113, 113, 0.15); color: var(--red); border: 1px solid rgba(248, 113, 113, 0.3); }}

        /* Expandable rows */
        .expand-row {{ display: none; }}
        .expand-row.visible {{ display: table-row; }}
        .expand-content {{
            padding: 20px; background: rgba(15, 15, 35, 0.5);
            font-size: 0.85rem; color: var(--text-secondary);
        }}
        .expand-content a {{ color: var(--accent-3); text-decoration: none; }}
        .expand-content a:hover {{ text-decoration: underline; }}
        .expand-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }}
        .expand-field {{ margin-bottom: 8px; }}
        .expand-label {{ font-weight: 600; color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        .expand-value {{ color: var(--text-primary); margin-top: 2px; }}
        .expand-toggle {{
            cursor: pointer; color: var(--accent-3); font-size: 1.2rem;
            text-align: center; width: 30px;
        }}

        /* --- AGENT ARCHITECTURE --- */
        .arch-flow {{
            display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
            justify-content: center; margin: 32px 0;
        }}
        .arch-step {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: var(--radius-sm); padding: 16px 20px;
            text-align: center; min-width: 140px;
        }}
        .arch-step .step-icon {{ font-size: 1.5rem; margin-bottom: 6px; }}
        .arch-step .step-name {{ font-size: 0.8rem; font-weight: 600; }}
        .arch-step .step-tech {{ font-size: 0.7rem; color: var(--text-muted); margin-top: 2px; }}
        .arch-arrow {{ color: var(--accent-1); font-size: 1.2rem; }}

        /* --- VERIFICATION --- */
        .verif-metrics {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px; margin-bottom: 32px;
        }}
        .verif-metric {{
            background: var(--bg-card); border: 1px solid var(--border);
            border-radius: var(--radius); padding: 24px; text-align: center;
        }}
        .verif-metric .metric-value {{
            font-size: 2.5rem; font-weight: 800;
        }}
        .verif-metric .metric-label {{
            font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;
            letter-spacing: 0.05em; margin-top: 4px;
        }}
        .verif-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
        .verif-table th {{
            background: var(--bg-secondary); padding: 10px 12px; text-align: left;
            font-weight: 600; color: var(--text-muted); text-transform: uppercase;
            font-size: 0.72rem; border-bottom: 2px solid var(--border);
        }}
        .verif-table td {{
            padding: 10px 12px; border-bottom: 1px solid var(--glass-border);
        }}
        .check {{ color: var(--green); }}
        .cross {{ color: var(--red); }}

        /* --- FOOTER --- */
        .footer {{
            padding: 60px 0 40px;
            border-top: 1px solid var(--border);
            text-align: center; color: var(--text-muted);
            font-size: 0.85rem;
        }}
        .footer-links {{
            display: flex; gap: 24px; justify-content: center; margin-bottom: 20px;
        }}
        .footer-links a {{
            color: var(--accent-3); text-decoration: none;
            padding: 8px 20px; border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            transition: all 0.2s;
        }}
        .footer-links a:hover {{
            background: var(--accent-1); color: white;
            border-color: var(--accent-1);
        }}

        /* --- FADE IN ANIMATION --- */
        .fade-in {{
            opacity: 0; transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }}
        .fade-in.visible {{
            opacity: 1; transform: translateY(0);
        }}

        /* --- RESPONSIVE --- */
        @media (max-width: 768px) {{
            .container {{ padding: 0 16px; }}
            .hero {{ min-height: 60vh; padding: 60px 16px; }}
            .hero h1 {{ font-size: 2rem; }}
            .hero-stats {{ gap: 20px; }}
            .charts-grid {{ grid-template-columns: 1fr; }}
            .table-controls {{ flex-direction: column; }}
            .search-input {{ min-width: 100%; }}
        }}

        /* scrollbar */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent-1); }}
    </style>
</head>
<body>
    <div class="bg-grid"></div>

    <!-- ===== HERO ===== -->
    <header class="hero" id="hero">
        <div class="hero-badge">🔬 Automated Research • AI-Verified • {total_apps} Apps</div>
        <h1>100-App Integration<br>Landscape</h1>
        <p class="hero-sub">
            Automated agent research across {total_apps} applications — authentication patterns, API surfaces,
            access models, and MCP servers — to identify where AI agent integrations are ready to build.
        </p>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="number">{total_apps}</div>
                <div class="label">Apps Researched</div>
            </div>
            <div class="hero-stat">
                <div class="number">{self_serve_count}</div>
                <div class="label">Self-Serve</div>
            </div>
            <div class="hero-stat">
                <div class="number">{buildable_count}</div>
                <div class="label">Buildable</div>
            </div>
            <div class="hero-stat">
                <div class="number">{oauth_count}</div>
                <div class="label">OAuth2 Supported</div>
            </div>
            <div class="hero-stat">
                <div class="number">{any_mcp}</div>
                <div class="label">Have MCP</div>
            </div>
        </div>
    </header>

    <!-- ===== KEY FINDINGS ===== -->
    <section id="findings">
        <div class="container">
            <div class="section-header fade-in">
                <h2>Key Findings</h2>
                <p>The headline patterns across all {total_apps} applications</p>
            </div>
            <div class="findings-grid fade-in" id="findingsGrid">
                <!-- Populated by JS -->
            </div>
        </div>
    </section>

    <!-- ===== CHARTS ===== -->
    <section id="charts">
        <div class="container">
            <div class="section-header fade-in">
                <h2>Pattern Analysis</h2>
                <p>Distribution of authentication, access models, API breadth, and buildability</p>
            </div>
            <div class="charts-grid fade-in">
                <div class="chart-card">
                    <h3>Authentication Methods</h3>
                    <div class="chart-container"><canvas id="authChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>Access Model Distribution</h3>
                    <div class="chart-container"><canvas id="accessChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>API Breadth</h3>
                    <div class="chart-container"><canvas id="breadthChart"></canvas></div>
                </div>
                <div class="chart-card">
                    <h3>Buildability Status</h3>
                    <div class="chart-container"><canvas id="buildChart"></canvas></div>
                </div>
            </div>
        </div>
    </section>

    <!-- ===== INTEGRATION MATRIX ===== -->
    <section id="matrix">
        <div class="container">
            <div class="section-header fade-in">
                <h2>Integration Readiness by Category</h2>
                <p>Buildability status across all 10 app categories</p>
            </div>
            <div class="chart-card fade-in">
                <div style="height:400px; position:relative;"><canvas id="matrixChart"></canvas></div>
            </div>
        </div>
    </section>

    <!-- ===== 100-APP TABLE ===== -->
    <section id="table-section">
        <div class="container">
            <div class="section-header fade-in">
                <h2>The 100-App Dataset</h2>
                <p>Click any row to expand details, evidence, and notes</p>
            </div>
            <div class="card fade-in" style="overflow-x:auto; padding: 24px;">
                <div class="table-controls">
                    <input type="text" class="search-input" id="searchInput" placeholder="🔍  Search apps...">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="ready">Ready</button>
                    <button class="filter-btn" data-filter="buildable">Buildable</button>
                    <button class="filter-btn" data-filter="needs_setup">Needs Setup</button>
                    <button class="filter-btn" data-filter="gated">Gated</button>
                    <button class="filter-btn" data-filter="blocked">Blocked</button>
                </div>
                <table class="data-table" id="dataTable">
                    <thead>
                        <tr>
                            <th style="width:30px"></th>
                            <th data-sort="name">App</th>
                            <th data-sort="category">Category</th>
                            <th data-sort="primary_auth">Auth</th>
                            <th data-sort="access_model">Access</th>
                            <th data-sort="api_breadth">API</th>
                            <th>MCP</th>
                            <th data-sort="buildability">Status</th>
                            <th data-sort="confidence">Conf.</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                    </tbody>
                </table>
            </div>
        </div>
    </section>

    <!-- ===== THE AGENT ===== -->
    <section id="agent">
        <div class="container">
            <div class="section-header fade-in">
                <h2>The Research Agent</h2>
                <p>Architecture and pipeline behind the automated research</p>
            </div>
            <div class="card fade-in">
                <div class="arch-flow">
                    <div class="arch-step">
                        <div class="step-icon">📋</div>
                        <div class="step-name">App List</div>
                        <div class="step-tech">100 apps JSON</div>
                    </div>
                    <div class="arch-arrow">→</div>
                    <div class="arch-step">
                        <div class="step-icon">🔍</div>
                        <div class="step-name">Web Search</div>
                        <div class="step-tech">DuckDuckGo</div>
                    </div>
                    <div class="arch-arrow">→</div>
                    <div class="arch-step">
                        <div class="step-icon">📄</div>
                        <div class="step-name">Doc Reader</div>
                        <div class="step-tech">httpx + trafilatura</div>
                    </div>
                    <div class="arch-arrow">→</div>
                    <div class="arch-step">
                        <div class="step-icon">🧠</div>
                        <div class="step-name">LLM Extraction</div>
                        <div class="step-tech">Gemini Flash</div>
                    </div>
                    <div class="arch-arrow">→</div>
                    <div class="arch-step">
                        <div class="step-icon">🔗</div>
                        <div class="step-name">MCP Search</div>
                        <div class="step-tech">GitHub/npm</div>
                    </div>
                    <div class="arch-arrow">→</div>
                    <div class="arch-step">
                        <div class="step-icon">✅</div>
                        <div class="step-name">Verification</div>
                        <div class="step-tech">3-layer system</div>
                    </div>
                </div>
                <div style="margin-top: 32px;">
                    <h3 style="margin-bottom: 16px; font-size: 1.1rem;">Pipeline Details</h3>
                    <div class="expand-grid">
                        <div>
                            <div class="expand-label">Per-App Pipeline</div>
                            <div class="expand-value" style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.7;">
                                1. Search for API docs + auth info (3 queries/app)<br>
                                2. Fetch & extract text from top 6 URLs<br>
                                3. Search for MCP servers on GitHub/npm<br>
                                4. LLM structured extraction (1 Gemini call)<br>
                                5. Automated confidence scoring
                            </div>
                        </div>
                        <div>
                            <div class="expand-label">Where the Human Was Needed</div>
                            <div class="expand-value" style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.7;">
                                • Obscure apps with no developer docs (fanbasis, Paygent)<br>
                                • Distinguishing official vs community MCP<br>
                                • Verifying paid-plan-only API access<br>
                                • Resolving conflicting auth documentation<br>
                                • Final accuracy validation on 20-app sample
                            </div>
                        </div>
                        <div>
                            <div class="expand-label">Tech Stack</div>
                            <div class="expand-value" style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.7;">
                                • Python 3.11+ with Pydantic models<br>
                                • Google Gemini Flash (free tier)<br>
                                • DuckDuckGo Search (no API key needed)<br>
                                • httpx + trafilatura for doc reading<br>
                                • Rich progress bars, resume-safe caching
                            </div>
                        </div>
                        <div>
                            <div class="expand-label">Performance</div>
                            <div class="expand-value" style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.7;">
                                • ~25-35 min full pipeline runtime<br>
                                • Resume-safe: caches each app result to disk<br>
                                • ~5 search queries + 1 LLM call per app<br>
                                • Works within Gemini free tier limits
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- ===== VERIFICATION ===== -->
    <section id="verification">
        <div class="container">
            <div class="section-header fade-in">
                <h2>Verification & Accuracy</h2>
                <p>Three-layer verification system with honest accuracy reporting</p>
            </div>

            <div class="verif-metrics fade-in">
                <div class="verif-metric">
                    <div class="metric-value" style="color: var(--accent-3);" id="verifSample">-</div>
                    <div class="metric-label">Apps Verified</div>
                </div>
                <div class="verif-metric">
                    <div class="metric-value" style="color: var(--green);" id="verifFieldAcc">-</div>
                    <div class="metric-label">Field Accuracy</div>
                </div>
                <div class="verif-metric">
                    <div class="metric-value" style="color: var(--blue);" id="verifRowAcc">-</div>
                    <div class="metric-label">Row Accuracy</div>
                </div>
                <div class="verif-metric">
                    <div class="metric-value" style="color: var(--yellow);" id="verifChecked">-</div>
                    <div class="metric-label">Fields Checked</div>
                </div>
            </div>

            <div class="card fade-in">
                <h3 style="margin-bottom: 16px;">Verification Layers</h3>
                <div class="expand-grid" style="margin-bottom: 24px;">
                    <div>
                        <div class="expand-label">Layer 1: Cross-Validation</div>
                        <div class="expand-value" style="color: var(--text-secondary); font-size: 0.85rem;">
                            Fresh web search for each verified app, LLM compares new evidence against original claims.
                        </div>
                    </div>
                    <div>
                        <div class="expand-label">Layer 2: Consistency Checks</div>
                        <div class="expand-value" style="color: var(--text-secondary); font-size: 0.85rem;">
                            Rule-based checks for logical contradictions (e.g., self-serve but no signup).
                        </div>
                    </div>
                    <div>
                        <div class="expand-label">Layer 3: Human Spot-Check</div>
                        <div class="expand-value" style="color: var(--text-secondary); font-size: 0.85rem;">
                            20-app sample manually verified against official docs, 2 per category.
                        </div>
                    </div>
                </div>
                <h3 style="margin-bottom: 12px;">Verification Sample Results</h3>
                <div style="overflow-x:auto;">
                    <table class="verif-table" id="verifTable">
                        <thead>
                            <tr>
                                <th>App</th>
                                <th>Field</th>
                                <th>Agent Says</th>
                                <th>Verified</th>
                                <th>✓/✗</th>
                                <th>Notes</th>
                            </tr>
                        </thead>
                        <tbody id="verifBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </section>

    <!-- ===== FOOTER ===== -->
    <footer class="footer">
        <div class="container">
            <div class="footer-links">
                <a href="#" id="downloadJson">📥 Download JSON</a>
                <a href="#" id="downloadCsv">📥 Download CSV</a>
                <a href="https://github.com" target="_blank">🔗 GitHub Repo</a>
            </div>
            <p>Built with Python, Google Gemini, DuckDuckGo Search · Composio AI Product Ops Research</p>
        </div>
    </footer>

    <!-- ===== EMBEDDED DATA ===== -->
    <script type="application/json" id="appData">{results_json}</script>
    <script type="application/json" id="analysisData">{analysis_json}</script>
    <script type="application/json" id="verificationData">{verification_json}</script>

    <script>
    // ===== DATA =====
    const apps = JSON.parse(document.getElementById('appData').textContent);
    const analysis = JSON.parse(document.getElementById('analysisData').textContent);
    const verification = JSON.parse(document.getElementById('verificationData').textContent);

    // ===== UTILITIES =====
    function buildabilityBadge(status) {{
        const cls = {{ready:'badge-ready',buildable:'badge-buildable',needs_setup:'badge-needs-setup',gated:'badge-gated',blocked:'badge-blocked'}}[status] || 'badge-unknown';
        return `<span class="badge ${{cls}}">${{status.replace('_',' ')}}</span>`;
    }}
    function confidenceBadge(conf) {{
        const cls = {{high:'badge-high',medium:'badge-medium',low:'badge-low'}}[conf] || 'badge-unknown';
        return `<span class="badge ${{cls}}">${{conf}}</span>`;
    }}

    // ===== KEY FINDINGS =====
    (function() {{
        const grid = document.getElementById('findingsGrid');
        const totalApps = apps.length;
        const selfServe = apps.filter(a => a.self_serve_signup).length;
        const selfServePct = Math.round(selfServe / totalApps * 100);
        const apiApps = apps.filter(a => a.has_public_api).length;
        const apiPct = Math.round(apiApps / totalApps * 100);

        // Top auth
        const authDist = analysis.primary_auth_distribution || {{}};
        const topAuth = Object.entries(authDist).sort((a,b) => b[1]-a[1])[0];

        // Top blocker
        const blockerDist = analysis.blocker_distribution || {{}};
        const topBlocker = Object.entries(blockerDist).sort((a,b) => b[1]-a[1])[0];

        const easyWins = (analysis.easy_wins || []).length;
        const mcpAny = (analysis.mcp_stats || {{}}).any_mcp || 0;

        const findings = [
            {{ icon: '🔓', stat: `${{selfServePct}}%`, desc: `${{selfServe}} of ${{totalApps}} apps offer self-serve developer signup — no sales call needed.` }},
            {{ icon: '🔑', stat: topAuth ? `${{topAuth[0]}}` : 'N/A', desc: topAuth ? `Dominates with ${{topAuth[1]}} apps using it as primary auth.` : 'Auth data not available.' }},
            {{ icon: '🌐', stat: `${{apiPct}}%`, desc: `${{apiApps}} apps have a documented public API. ${{totalApps - apiApps}} lack one entirely.` }},
            {{ icon: '🚫', stat: topBlocker ? `${{topBlocker[1]}} apps` : 'N/A', desc: topBlocker ? `"${{topBlocker[0].replace('_',' ')}}" is the most common integration blocker.` : 'No dominant blocker.' }},
            {{ icon: '🚀', stat: `${{easyWins}}`, desc: `Apps that are self-serve + broad API + buildable today — the easy wins for Composio.` }},
            {{ icon: '🔗', stat: `${{mcpAny}}`, desc: `Apps with an existing MCP server (official or community). The rest need to be built from API.` }},
        ];
        grid.innerHTML = findings.map(f => `
            <div class="finding-card">
                <div class="icon">${{f.icon}}</div>
                <div class="stat">${{f.stat}}</div>
                <div class="desc">${{f.desc}}</div>
            </div>
        `).join('');
    }})();

    // ===== CHARTS =====
    const chartColors = ['#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#60a5fa','#34d399','#fbbf24','#fb923c','#f87171','#f472b6'];
    Chart.defaults.color = '#a0a0c0';
    Chart.defaults.borderColor = 'rgba(99,102,241,0.1)';

    function makeDonut(canvasId, data, label) {{
        const labels = Object.keys(data);
        const values = Object.values(data);
        new Chart(document.getElementById(canvasId), {{
            type: 'doughnut',
            data: {{ labels, datasets: [{{ data: values, backgroundColor: chartColors.slice(0, labels.length), borderWidth: 0 }}] }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right', labels: {{ padding: 16, usePointStyle: true, pointStyle: 'circle' }} }}
                }}
            }}
        }});
    }}

    makeDonut('authChart', analysis.primary_auth_distribution || {{}});
    makeDonut('accessChart', analysis.access_distribution || {{}});
    makeDonut('breadthChart', analysis.api_breadth_distribution || {{}});
    makeDonut('buildChart', analysis.buildability_distribution || {{}});

    // Stacked bar: buildability by category
    (function() {{
        const catBuild = analysis.buildability_by_category || {{}};
        const cats = Object.keys(catBuild);
        const statuses = ['ready','buildable','needs_setup','gated','blocked'];
        const statusColors = {{'ready':'#34d399','buildable':'#60a5fa','needs_setup':'#fbbf24','gated':'#fb923c','blocked':'#f87171'}};
        const datasets = statuses.map(s => ({{
            label: s.replace('_',' '),
            data: cats.map(c => (catBuild[c] || {{}})[s] || 0),
            backgroundColor: statusColors[s],
        }}));
        new Chart(document.getElementById('matrixChart'), {{
            type: 'bar',
            data: {{ labels: cats.map(c => c.length > 25 ? c.slice(0,22)+'...' : c), datasets }},
            options: {{
                responsive: true, maintainAspectRatio: false,
                scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, beginAtZero: true }} }},
                plugins: {{ legend: {{ labels: {{ usePointStyle: true, pointStyle: 'circle' }} }} }}
            }}
        }});
    }})();

    // ===== DATA TABLE =====
    const tbody = document.getElementById('tableBody');
    let currentFilter = 'all';
    let searchTerm = '';

    function renderTable() {{
        let filtered = apps;
        if (currentFilter !== 'all') filtered = filtered.filter(a => a.buildability === currentFilter);
        if (searchTerm) {{
            const s = searchTerm.toLowerCase();
            filtered = filtered.filter(a =>
                a.name.toLowerCase().includes(s) ||
                a.category.toLowerCase().includes(s) ||
                (a.primary_auth || '').toLowerCase().includes(s) ||
                (a.description || '').toLowerCase().includes(s)
            );
        }}
        tbody.innerHTML = filtered.map(a => `
            <tr class="data-row" data-id="${{a.id}}">
                <td class="expand-toggle">▶</td>
                <td class="app-name">${{a.name}}</td>
                <td><span class="cat-badge">${{a.category}}</span></td>
                <td>${{a.primary_auth || '—'}}</td>
                <td>${{(a.access_model || '—').replace('_',' ')}}</td>
                <td>${{(a.api_breadth || '—').replace('_',' ')}}</td>
                <td>${{a.has_official_mcp ? '✅' : a.has_community_mcp ? '🔵' : '—'}}</td>
                <td>${{buildabilityBadge(a.buildability || 'unknown')}}</td>
                <td>${{confidenceBadge(a.confidence || 'low')}}</td>
            </tr>
            <tr class="expand-row" data-expand="${{a.id}}">
                <td colspan="9">
                    <div class="expand-content">
                        <div class="expand-grid">
                            <div>
                                <div class="expand-field"><div class="expand-label">Description</div><div class="expand-value">${{a.description || '—'}}</div></div>
                                <div class="expand-field"><div class="expand-label">Auth Methods</div><div class="expand-value">${{(a.auth_methods || []).join(', ') || '—'}}</div></div>
                                <div class="expand-field"><div class="expand-label">API Types</div><div class="expand-value">${{(a.api_types || []).join(', ') || '—'}}</div></div>
                            </div>
                            <div>
                                <div class="expand-field"><div class="expand-label">Webhooks</div><div class="expand-value">${{a.has_webhooks ? 'Yes' : 'No'}}</div></div>
                                <div class="expand-field"><div class="expand-label">Official SDK</div><div class="expand-value">${{a.has_official_sdk ? 'Yes' : 'No'}}</div></div>
                                <div class="expand-field"><div class="expand-label">Primary Blocker</div><div class="expand-value">${{a.primary_blocker || 'None'}}</div></div>
                            </div>
                            <div>
                                <div class="expand-field"><div class="expand-label">API Docs</div><div class="expand-value">${{a.api_docs_url ? `<a href="${{a.api_docs_url}}" target="_blank">${{a.api_docs_url}}</a>` : '—'}}</div></div>
                                <div class="expand-field"><div class="expand-label">MCP URL</div><div class="expand-value">${{a.mcp_url ? `<a href="${{a.mcp_url}}" target="_blank">${{a.mcp_url}}</a>` : '—'}}</div></div>
                                <div class="expand-field"><div class="expand-label">Notes</div><div class="expand-value">${{a.notes || '—'}}</div></div>
                            </div>
                            <div>
                                <div class="expand-field"><div class="expand-label">Evidence</div><div class="expand-value">${{(a.evidence || []).map(e => `<div style="margin-bottom:4px;">• ${{e.claim}} ${{e.url ? `<a href="${{e.url}}" target="_blank">[source]</a>` : ''}}</div>`).join('') || '—'}}</div></div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `).join('');

        // Re-attach expand listeners
        document.querySelectorAll('.data-row').forEach(row => {{
            row.addEventListener('click', () => {{
                const id = row.dataset.id;
                const expandRow = document.querySelector(`.expand-row[data-expand="${{id}}"]`);
                const toggle = row.querySelector('.expand-toggle');
                expandRow.classList.toggle('visible');
                toggle.textContent = expandRow.classList.contains('visible') ? '▼' : '▶';
            }});
        }});
    }}

    // Search
    document.getElementById('searchInput').addEventListener('input', (e) => {{
        searchTerm = e.target.value;
        renderTable();
    }});

    // Filters
    document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderTable();
        }});
    }});

    renderTable();

    // ===== VERIFICATION =====
    (function() {{
        document.getElementById('verifSample').textContent = verification.sample_size || 0;
        document.getElementById('verifFieldAcc').textContent = verification.field_accuracy ? (verification.field_accuracy * 100).toFixed(1) + '%' : '—';
        document.getElementById('verifRowAcc').textContent = verification.row_accuracy ? (verification.row_accuracy * 100).toFixed(1) + '%' : '—';
        document.getElementById('verifChecked').textContent = verification.total_fields_checked || 0;

        const vBody = document.getElementById('verifBody');
        const vResults = verification.results || [];
        vBody.innerHTML = vResults.slice(0, 50).map(v => `
            <tr>
                <td style="font-weight:600;">${{v.app_name}}</td>
                <td>${{v.field_name}}</td>
                <td>${{v.agent_value}}</td>
                <td>${{v.verified_value}}</td>
                <td class="${{v.is_correct ? 'check' : 'cross'}}">${{v.is_correct ? '✓' : '✗'}}</td>
                <td style="color:var(--text-muted);font-size:0.8rem;">${{v.notes || ''}}</td>
            </tr>
        `).join('');
    }})();

    // ===== DOWNLOADS =====
    document.getElementById('downloadJson').addEventListener('click', (e) => {{
        e.preventDefault();
        const blob = new Blob([JSON.stringify(apps, null, 2)], {{ type: 'application/json' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'composio-100-app-research.json'; a.click();
    }});
    document.getElementById('downloadCsv').addEventListener('click', (e) => {{
        e.preventDefault();
        const headers = ['id','name','category','description','primary_auth','auth_methods','access_model','self_serve_signup','has_public_api','api_types','api_breadth','api_docs_url','has_webhooks','has_official_sdk','has_official_mcp','has_community_mcp','buildability','primary_blocker','blocker_type','confidence','notes'];
        const rows = apps.map(a => headers.map(h => {{
            let v = a[h];
            if (Array.isArray(v)) v = v.join('; ');
            if (typeof v === 'string' && (v.includes(',') || v.includes('"'))) v = '"' + v.replace(/"/g, '""') + '"';
            return v ?? '';
        }}).join(','));
        const csv = headers.join(',') + '\\n' + rows.join('\\n');
        const blob = new Blob([csv], {{ type: 'text/csv' }});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'composio-100-app-research.csv'; a.click();
    }});

    // ===== FADE IN ON SCROLL =====
    const observer = new IntersectionObserver((entries) => {{
        entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('visible'); }});
    }}, {{ threshold: 0.1 }});
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
    </script>
</body>
</html>"""

    return html


def main():
    dataset = load_dataset()
    html = generate_html(dataset)

    output_path = config.OUTPUT_DIR / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML report generated: {output_path}")
    print(f"   Open in browser or deploy to Vercel.")


if __name__ == "__main__":
    main()
