"""
styles.py — CSS global de la aplicación BDO IDU-1556-2025
Modo claro y oscuro con variables CSS. Sidebar siempre oscuro (estilo panel IDU).
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ════════════════════════════════════════════
   VARIABLES — MODO CLARO (por defecto)
   ════════════════════════════════════════════ */
:root {
    /* Fondos */
    --bg-app:          #f2f4f8;
    --bg-card:         #ffffff;
    --bg-card-hover:   #f7f9ff;
    --bg-sidebar:      #1c2340;
    --bg-sidebar-item: rgba(255,255,255,0.06);

    /* Bordes */
    --border:          #dde2eb;
    --border-strong:   #b0bad0;

    /* Texto */
    --text-primary:    #111827;
    --text-secondary:  #374151;
    --text-muted:      #6b7280;
    --text-sidebar:    #c8d0e0;
    --text-sidebar-muted: #7a8aa0;

    /* Acentos */
    --accent-blue:     #1a56db;
    --accent-blue-lt:  #dbeafe;
    --accent-green:    #0d7a4e;
    --accent-green-lt: #d1fae5;
    --accent-red:      #b91c1c;
    --accent-red-lt:   #fee2e2;
    --accent-orange:   #c2410c;
    --accent-orange-lt:#ffedd5;
    --accent-purple:   #6d28d9;
    --accent-purple-lt:#ede9fe;
    --accent-teal:     #0f766e;
    --accent-teal-lt:  #ccfbf1;

    /* Nav */
    --nav-cat-color:    #7a8aa0;
    --nav-cat-hi-color: #58a6ff;
    --nav-active-bg:    rgba(255,255,255,0.14);
    --nav-active-border:#58a6ff;
    --nav-active-text:  #ffffff;
    --nav-idle-text:    #a8b8cc;

    /* Badges de estado */
    --badge-borrador-bg:  #f1f5f9; --badge-borrador-fg: #475569;
    --badge-revisado-bg:  #d1fae5; --badge-revisado-fg: #065f46;
    --badge-aprobado-bg:  #dbeafe; --badge-aprobado-fg: #1e40af;
    --badge-devuelto-bg:  #fee2e2; --badge-devuelto-fg: #991b1b;

    /* KPI */
    --kpi-value-color: #111827;
}

/* ════════════════════════════════════════════
   VARIABLES — MODO OSCURO
   ════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-app:          #0d1117;
        --bg-card:         #161b22;
        --bg-card-hover:   #1c2333;
        --bg-sidebar:      #010409;
        --bg-sidebar-item: rgba(255,255,255,0.05);

        --border:          #21262d;
        --border-strong:   #30363d;

        --text-primary:    #e6edf3;
        --text-secondary:  #c9d1d9;
        --text-muted:      #8b949e;
        --text-sidebar:    #c9d1d9;
        --text-sidebar-muted: #6e7681;

        --accent-blue:     #58a6ff;
        --accent-blue-lt:  #1a3255;
        --accent-green:    #56d364;
        --accent-green-lt: #0d2d1f;
        --accent-red:      #f85149;
        --accent-red-lt:   #3d1e1e;
        --accent-orange:   #ffa657;
        --accent-orange-lt:#3d2200;
        --accent-purple:   #d2a8ff;
        --accent-purple-lt:#2d1f4e;
        --accent-teal:     #2dd4bf;
        --accent-teal-lt:  #0d2d2a;

        --nav-cat-color:    #6e7681;
        --nav-cat-hi-color: #58a6ff;
        --nav-active-bg:    rgba(88,166,255,0.14);
        --nav-active-border:#58a6ff;
        --nav-active-text:  #e6edf3;
        --nav-idle-text:    #8b949e;

        --badge-borrador-bg:  #21262d; --badge-borrador-fg: #8b949e;
        --badge-revisado-bg:  #0d2d1f; --badge-revisado-fg: #56d364;
        --badge-aprobado-bg:  #1a3255; --badge-aprobado-fg: #58a6ff;
        --badge-devuelto-bg:  #3d1e1e; --badge-devuelto-fg: #f85149;

        --kpi-value-color: #e6edf3;
    }
}

/* ════════════════════════════════════════════
   BASE
   ════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp { background: var(--bg-app); color: var(--text-primary); }

/* ════════════════════════════════════════════
   SIDEBAR — siempre oscuro (estilo panel IDU)
   ════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
section[data-testid="stSidebar"] * {
    color: var(--text-sidebar) !important;
}
section[data-testid="stSidebar"] .stMarkdown p {
    color: var(--text-sidebar-muted) !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: var(--bg-sidebar-item) !important;
    color: var(--nav-idle-text) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.85rem !important;
    text-align: left !important;
    padding: 0.4rem 0.75rem !important;
    margin-bottom: 2px !important;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.10) !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,0.15) !important;
}

/* Nav item activo (no clickable, resaltado) */
.nav-item-active {
    display: block;
    background: var(--nav-active-bg);
    border-left: 3px solid var(--nav-active-border);
    border-radius: 6px;
    padding: 0.45rem 0.75rem;
    margin-bottom: 2px;
    color: var(--nav-active-text) !important;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    width: 100%;
    box-sizing: border-box;
}

/* Categoría normal */
.nav-cat {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.60rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--nav-cat-color) !important;
    padding: 0.65rem 0 0.2rem 0;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin-top: 0.5rem;
}
.nav-cat:first-of-type { border-top: none; margin-top: 0; }

/* Categoría destacada */
.nav-cat-hi {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.60rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--nav-cat-hi-color) !important;
    padding: 0.65rem 0 0.2rem 0;
    border-top: 1px solid rgba(88,166,255,0.20);
    margin-top: 0.6rem;
}

/* Chips de estado rápido en sidebar */
.stat-row  { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.stat-chip {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
}

/* ════════════════════════════════════════════
   KPI CARDS
   ════════════════════════════════════════════ */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    background: var(--border);
    border-radius: 10px 0 0 10px;
}
.kpi-card.accent-blue::before   { background: var(--accent-blue); }
.kpi-card.accent-green::before  { background: var(--accent-green); }
.kpi-card.accent-red::before    { background: var(--accent-red); }
.kpi-card.accent-orange::before { background: var(--accent-orange); }
.kpi-card.accent-purple::before { background: var(--accent-purple); }
.kpi-card.accent-teal::before   { background: var(--accent-teal); }

.kpi-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
    font-family: 'IBM Plex Mono', monospace;
}
.kpi-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--kpi-value-color);
    line-height: 1.2;
    font-variant-numeric: tabular-nums;
}
.kpi-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

/* Colores de valor */
.kpi-blue   { color: var(--accent-blue)   !important; }
.kpi-green  { color: var(--accent-green)  !important; }
.kpi-red    { color: var(--accent-red)    !important; }
.kpi-orange { color: var(--accent-orange) !important; }
.kpi-purple { color: var(--accent-purple) !important; }
.kpi-teal   { color: var(--accent-teal)   !important; }
/* Aliases semánticos */
.kpi-accent { color: var(--accent-green)  !important; }
.kpi-warn   { color: var(--accent-orange) !important; }
.kpi-danger { color: var(--accent-red)    !important; }
.kpi-info   { color: var(--accent-blue)   !important; }

/* ════════════════════════════════════════════
   SECTION BADGE (estilo IDU)
   ════════════════════════════════════════════ */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 14px;
    border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.70rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}
.sb-blue   { background: var(--accent-blue-lt);   color: var(--accent-blue);   }
.sb-green  { background: var(--accent-green-lt);  color: var(--accent-green);  }
.sb-red    { background: var(--accent-red-lt);    color: var(--accent-red);    }
.sb-orange { background: var(--accent-orange-lt); color: var(--accent-orange); }
.sb-purple { background: var(--accent-purple-lt); color: var(--accent-purple); }
.sb-teal   { background: var(--accent-teal-lt);   color: var(--accent-teal);   }

/* ════════════════════════════════════════════
   STATUS BADGES
   ════════════════════════════════════════════ */
.badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 9px;
    border-radius: 4px;
    letter-spacing: 0.06em;
}
.badge-borrador { background: var(--badge-borrador-bg); color: var(--badge-borrador-fg); }
.badge-revisado { background: var(--badge-revisado-bg); color: var(--badge-revisado-fg); }
.badge-aprobado { background: var(--badge-aprobado-bg); color: var(--badge-aprobado-fg); }
.badge-devuelto { background: var(--badge-devuelto-bg); color: var(--badge-devuelto-fg); }

/* ════════════════════════════════════════════
   TIPOGRAFÍA Y CONTENEDORES
   ════════════════════════════════════════════ */
.stDataFrame { border-radius: 8px; overflow: hidden; }

.stButton > button {
    font-family: 'IBM Plex Sans', sans-serif;
    border-radius: 6px;
}

hr { border-color: var(--border); }

details summary {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.84rem;
    color: var(--text-secondary);
}

h1, h2, h3 {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 700;
    color: var(--text-primary);
}
h3 {
    border-bottom: 2px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1.1rem;
}

.login-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2.5rem 2rem;
}
</style>
"""
