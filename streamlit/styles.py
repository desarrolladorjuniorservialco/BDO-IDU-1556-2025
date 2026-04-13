"""
styles.py — CSS global de la aplicacion BDO IDU-1556-2025
Paleta institucional Bogota / IDU · Modo claro y oscuro con variables CSS.
Sidebar siempre oscuro (estilo panel IDU).
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&family=Barlow+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ════════════════════════════════════════════
   VARIABLES — MODO CLARO (por defecto)
   Paleta institucional Bogota IDU
   ════════════════════════════════════════════ */
:root {
    /* --- Identidad Central (Primarios) --- */
    --bogota-blue-deep:  #002D57;
    --bogota-blue-active:#004B8D;
    --bogota-yellow:     #FFD200;
    --bogota-gold:       #E6BC00;

    /* --- Paleta IDU mapeada --- */
    --idu-navy:        #002D57;
    --idu-navy-deep:   #002D57;
    --idu-navy-lt:     #cce0f5;
    --idu-teal:        #198754;
    --idu-teal-lt:     #d1f2dc;
    --idu-amber:       #FFD200;
    --idu-amber-lt:    #fff8d6;

    /* Fondos */
    --bg-app:          #F8F9FA;
    --bg-card:         #FFFFFF;
    --bg-card-hover:   #f0f4ff;
    --bg-sidebar:      #002D57;
    --bg-sidebar-item: rgba(255,255,255,0.06);
    --bg-inset:        #F0F2F5;

    /* Bordes */
    --border:          #DEE2E6;
    --border-strong:   #ADB5BD;

    /* Texto */
    --text-primary:    #212529;
    --text-secondary:  #495057;
    --text-muted:      #6C757D;
    --text-sidebar:    #E6EDF3;
    --text-sidebar-muted: #8B949E;

    /* Acentos semanticos */
    --accent-blue:     #002D57;
    --accent-blue-lt:  #cce0f5;
    --accent-green:    #198754;
    --accent-green-lt: #d1f2dc;
    --accent-red:      #B02A37;
    --accent-red-lt:   #f5d0d3;
    --accent-orange:   #FD7E14;
    --accent-orange-lt:#ffe8cc;
    --accent-purple:   #6f42c1;
    --accent-purple-lt:#e8dcf8;
    --accent-teal:     #0D6EFD;
    --accent-teal-lt:  #cfe2ff;

    /* Semantica de ejecucion */
    --exec-completado: #198754;
    --exec-progreso:   #0D6EFD;
    --exec-atrasado:   #FD7E14;
    --exec-critico:    #B02A37;
    --exec-planeacion: #ADB5BD;

    /* Nav */
    --nav-cat-color:    #8B949E;
    --nav-cat-hi-color: #FFD200;
    --nav-active-bg:    rgba(255,210,0,0.12);
    --nav-active-border:#FFD200;
    --nav-active-text:  #ffffff;
    --nav-idle-text:    #8B949E;

    /* Badges de estado */
    --badge-borrador-bg:  #e9ecef; --badge-borrador-fg: #495057;
    --badge-revisado-bg:  #cfe2ff; --badge-revisado-fg: #084298;
    --badge-aprobado-bg:  #d1f2dc; --badge-aprobado-fg: #0f5132;
    --badge-devuelto-bg:  #f5d0d3; --badge-devuelto-fg: #842029;

    /* KPI */
    --kpi-value-color:  #212529;

    /* Botones de accion */
    --btn-approve-bg:   #198754;
    --btn-approve-fg:   #ffffff;
    --btn-return-bg:    #B02A37;
    --btn-return-fg:    #ffffff;

    /* CTA (Bogota Yellow) */
    --btn-cta-bg:       #FFD200;
    --btn-cta-fg:       #212529;
    --btn-cta-border:   #E6BC00;
}

/* ════════════════════════════════════════════
   VARIABLES — MODO OSCURO
   Superficies por elevacion, texto sin glare
   ════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
    :root {
        --idu-navy:        #1F6FEB;
        --idu-navy-deep:   #58A6FF;
        --idu-navy-lt:     #1a2744;
        --idu-teal:        #3fb950;
        --idu-teal-lt:     #0d2818;
        --idu-amber:       #FFD200;
        --idu-amber-lt:    #3d2800;

        /* Superficies por elevacion */
        --bg-app:          #0B1117;
        --bg-card:         #161B22;
        --bg-card-hover:   #1c2330;
        --bg-sidebar:      #0B1117;
        --bg-sidebar-item: rgba(255,255,255,0.05);
        --bg-inset:        #161B22;

        /* Bordes */
        --border:          #30363D;
        --border-strong:   #484f58;

        /* Texto sin glare */
        --text-primary:    #E6EDF3;
        --text-secondary:  #c9d1d9;
        --text-muted:      #8B949E;
        --text-sidebar:    #E6EDF3;
        --text-sidebar-muted: #8B949E;

        /* Acentos oscuros */
        --accent-blue:     #1F6FEB;
        --accent-blue-lt:  #1a2744;
        --accent-green:    #3fb950;
        --accent-green-lt: #0d2818;
        --accent-red:      #f85149;
        --accent-red-lt:   #3d1010;
        --accent-orange:   #FD7E14;
        --accent-orange-lt:#3d2200;
        --accent-purple:   #bc8cff;
        --accent-purple-lt:#2d1f60;
        --accent-teal:     #58A6FF;
        --accent-teal-lt:  #0d3050;

        /* Semantica de ejecucion oscura */
        --exec-completado: #3fb950;
        --exec-progreso:   #58A6FF;
        --exec-atrasado:   #FD7E14;
        --exec-critico:    #f85149;
        --exec-planeacion: #484f58;

        /* Nav */
        --nav-cat-color:    #8B949E;
        --nav-cat-hi-color: #FFD200;
        --nav-active-bg:    rgba(255,210,0,0.10);
        --nav-active-border:#FFD200;
        --nav-active-text:  #E6EDF3;
        --nav-idle-text:    #8B949E;

        /* Badges */
        --badge-borrador-bg:  #21262D; --badge-borrador-fg: #8B949E;
        --badge-revisado-bg:  #0d3050; --badge-revisado-fg: #58A6FF;
        --badge-aprobado-bg:  #0d2818; --badge-aprobado-fg: #3fb950;
        --badge-devuelto-bg:  #3d1010; --badge-devuelto-fg: #f85149;

        --kpi-value-color:  #E6EDF3;

        --btn-approve-bg:   #3fb950;
        --btn-approve-fg:   #0d1117;
        --btn-return-bg:    #f85149;
        --btn-return-fg:    #0d1117;

        --btn-cta-bg:       #FFD200;
        --btn-cta-fg:       #0B1117;
        --btn-cta-border:   #E6BC00;
    }
}

/* ════════════════════════════════════════════
   BASE
   ════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: 'Barlow', 'IBM Plex Sans', sans-serif;
}
.stApp { background: var(--bg-app); color: var(--text-primary); }

/* ════════════════════════════════════════════
   OCULTAR NAVEGACION AUTOMATICA DE STREAMLIT
   (lista de paginas auto-detectadas del sidebar)
   ════════════════════════════════════════════ */
[data-testid="stSidebarNav"],
section[data-testid="stSidebar"] nav,
section[data-testid="stSidebar"] ul {
    display: none !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* ════════════════════════════════════════════
   SIDEBAR — siempre oscuro (estilo panel IDU)
   ════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid rgba(31,111,235,0.12);
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
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 0.4rem 0.75rem !important;
    margin-bottom: 2px !important;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(0,75,141,0.35) !important;
    color: #ffffff !important;
    border-color: rgba(0,75,141,0.5) !important;
}

/* Nav item activo */
.nav-item-active {
    display: block;
    background: var(--nav-active-bg);
    border-left: 3px solid var(--nav-active-border);
    border-radius: 6px;
    padding: 0.45rem 0.75rem;
    margin-bottom: 2px;
    color: var(--nav-active-text) !important;
    font-family: 'Barlow', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
    width: 100%;
    box-sizing: border-box;
}

/* Categoria normal */
.nav-cat {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--nav-cat-color) !important;
    padding: 0.65rem 0 0.2rem 0;
    border-top: 1px solid rgba(255,255,255,0.06);
    margin-top: 0.5rem;
}
.nav-cat:first-of-type { border-top: none; margin-top: 0; }

/* Categoria destacada */
.nav-cat-hi {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--nav-cat-hi-color) !important;
    padding: 0.65rem 0 0.2rem 0;
    border-top: 1px solid rgba(255,210,0,0.18);
    margin-top: 0.6rem;
}

/* Chips de estado */
.stat-row  { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.stat-chip {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
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
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: var(--text-muted);
    margin-bottom: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}
.kpi-value {
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--kpi-value-color);
    line-height: 1.2;
    font-variant-numeric: tabular-nums;
    font-family: 'Barlow', sans-serif;
}
.kpi-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
    font-family: 'Barlow', sans-serif;
}

/* Colores de valor */
.kpi-blue   { color: var(--accent-blue)   !important; }
.kpi-green  { color: var(--accent-green)  !important; }
.kpi-red    { color: var(--accent-red)    !important; }
.kpi-orange { color: var(--accent-orange) !important; }
.kpi-purple { color: var(--accent-purple) !important; }
.kpi-teal   { color: var(--accent-teal)   !important; }
.kpi-accent { color: var(--accent-green)  !important; }
.kpi-warn   { color: var(--accent-orange) !important; }
.kpi-danger { color: var(--accent-red)    !important; }
.kpi-info   { color: var(--accent-blue)   !important; }

/* ════════════════════════════════════════════
   FILTROS — contraste garantizado
   ════════════════════════════════════════════ */
.stTextInput label, .stSelectbox label,
.stDateInput label, .stMultiSelect label,
.stRadio label, .stCheckbox label {
    color: var(--text-primary) !important;
    font-family: 'Barlow', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
.filter-form-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem 0.5rem;
    margin-bottom: 1rem;
}
.filter-form-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.63rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    margin-bottom: 0.75rem;
}

/* ════════════════════════════════════════════
   INPUTS — Oscurecer al enfocar / tener contenido
   ════════════════════════════════════════════ */
.stTextInput input,
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
.stDateInput input {
    transition: background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

/* Estado focus: borde azul activo + fondo ligeramente mas oscuro */
.stTextInput input:focus,
.stDateInput input:focus {
    background-color: #edf2f9 !important;
    border-color: var(--bogota-blue-active, #004B8D) !important;
    box-shadow: 0 0 0 2px rgba(0,75,141,0.18) !important;
}

/* Selectbox / multiselect al abrir (estado activo) */
.stSelectbox [data-baseweb="select"] > div[aria-expanded="true"],
.stSelectbox [data-baseweb="select"]:focus-within > div,
.stMultiSelect [data-baseweb="select"] > div[aria-expanded="true"],
.stMultiSelect [data-baseweb="select"]:focus-within > div {
    background-color: #edf2f9 !important;
    border-color: var(--bogota-blue-active, #004B8D) !important;
    box-shadow: 0 0 0 2px rgba(0,75,141,0.18) !important;
}

/* Multiselect con tags (tiene contenido seleccionado) */
.stMultiSelect [data-baseweb="tag"] {
    background-color: var(--accent-blue-lt) !important;
    color: var(--accent-blue) !important;
    font-weight: 700 !important;
}
.stMultiSelect [data-baseweb="select"]:has([data-baseweb="tag"]) > div {
    background-color: #edf2f9 !important;
    border-color: var(--bogota-blue-active, #004B8D) !important;
}

/* Input con contenido (no placeholder) */
.stTextInput input:not(:placeholder-shown),
.stDateInput input:not(:placeholder-shown) {
    background-color: #edf2f9 !important;
    border-color: #ADB5BD !important;
}

/* Dark mode overrides para inputs */
@media (prefers-color-scheme: dark) {
    .stTextInput input:focus,
    .stDateInput input:focus {
        background-color: #21262D !important;
        border-color: #58A6FF !important;
        box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
    }
    .stSelectbox [data-baseweb="select"] > div[aria-expanded="true"],
    .stSelectbox [data-baseweb="select"]:focus-within > div,
    .stMultiSelect [data-baseweb="select"] > div[aria-expanded="true"],
    .stMultiSelect [data-baseweb="select"]:focus-within > div {
        background-color: #21262D !important;
        border-color: #58A6FF !important;
        box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
    }
    .stMultiSelect [data-baseweb="select"]:has([data-baseweb="tag"]) > div {
        background-color: #21262D !important;
        border-color: #58A6FF !important;
    }
    .stTextInput input:not(:placeholder-shown),
    .stDateInput input:not(:placeholder-shown) {
        background-color: #21262D !important;
        border-color: #484f58 !important;
    }
}

/* ════════════════════════════════════════════
   SECTION BADGE (estilo IDU)
   ════════════════════════════════════════════ */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 16px;
    border-radius: 20px;
    font-family: 'Barlow Condensed', 'Barlow', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.09em;
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
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.67rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 4px;
    letter-spacing: 0.05em;
}
.badge-borrador { background: var(--badge-borrador-bg); color: var(--badge-borrador-fg); }
.badge-revisado { background: var(--badge-revisado-bg); color: var(--badge-revisado-fg); }
.badge-aprobado { background: var(--badge-aprobado-bg); color: var(--badge-aprobado-fg); }
.badge-devuelto { background: var(--badge-devuelto-bg); color: var(--badge-devuelto-fg); }

/* ════════════════════════════════════════════
   CONTRATO — HEADER Y FICHAS
   ════════════════════════════════════════════ */
.contract-header {
    background: linear-gradient(135deg, #002D57 0%, #004B8D 100%);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
    color: #fff;
    position: relative;
    overflow: hidden;
}
.contract-id {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    color: rgba(255,255,255,0.55);
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
}
.contract-name {
    font-family: 'Barlow', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #fff;
    line-height: 1.35;
    margin-bottom: 0.9rem;
}
.contract-meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.7rem 1.2rem;
}
.contract-meta-item { }
.contract-meta-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.48);
    margin-bottom: 0.18rem;
}
.contract-meta-value {
    font-family: 'Barlow', sans-serif;
    font-size: 0.88rem;
    font-weight: 600;
    color: rgba(255,255,255,0.92);
    line-height: 1.3;
}

/* ════════════════════════════════════════════
   BARRA DE PROGRESO DE TIEMPO
   ════════════════════════════════════════════ */
.timeline-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.75rem;
}
.timeline-label-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.55rem;
}
.timeline-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
}
.timeline-pct {
    font-family: 'Barlow', sans-serif;
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text-primary);
}
.timeline-bar-wrap {
    background: var(--border);
    border-radius: 6px;
    height: 14px;
    overflow: hidden;
    position: relative;
}
.timeline-bar-fill {
    height: 100%;
    border-radius: 6px;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 6px;
    transition: width 0.6s ease;
}
.timeline-bar-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    font-weight: 700;
    color: rgba(255,255,255,0.9);
    white-space: nowrap;
}
.timeline-dates {
    display: flex;
    justify-content: space-between;
    margin-top: 0.45rem;
}
.timeline-date-item {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    color: var(--text-muted);
}

/* ════════════════════════════════════════════
   PANEL DE APROBACION
   ════════════════════════════════════════════ */
.approval-panel {
    background: var(--bg-inset);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.9rem 1rem;
}
.approval-panel-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    margin-bottom: 0.6rem;
}
.approval-history {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.6rem;
    font-family: 'Barlow', sans-serif;
    font-size: 0.78rem;
    color: var(--text-secondary);
}
.approval-history-item {
    padding: 0.3rem 0;
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.approval-history-item:last-child { border-bottom: none; }
.approval-history-role {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
}

/* ════════════════════════════════════════════
   GRILLA DE FOTOS
   ════════════════════════════════════════════ */
.photo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.5rem;
    margin-top: 0.5rem;
}
.photo-thumb {
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid var(--border);
    aspect-ratio: 1;
    background: var(--bg-inset);
}
.photo-thumb img {
    width: 100%; height: 100%;
    object-fit: cover;
    display: block;
}

/* ════════════════════════════════════════════
   TABLA DE SEGUIMIENTO (adiciones / prorrogas)
   ════════════════════════════════════════════ */
.tracking-table-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.75rem;
}
.tracking-table-header {
    background: var(--bg-inset);
    border-bottom: 2px solid var(--border);
    padding: 0.65rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.tracking-table-title {
    font-family: 'Barlow', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.tracking-table-count {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--text-muted);
    background: var(--border);
    border-radius: 10px;
    padding: 1px 8px;
}

/* ════════════════════════════════════════════
   INFO PILLS (indicadores pequenos en filas)
   ════════════════════════════════════════════ */
.info-pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem;
    font-weight: 600;
    background: var(--bg-inset);
    color: var(--text-secondary);
    border: 1px solid var(--border);
    margin-right: 4px;
    margin-bottom: 4px;
}
.info-pill.blue   { background: var(--accent-blue-lt);   color: var(--accent-blue);   border-color: var(--accent-blue-lt); }
.info-pill.green  { background: var(--accent-green-lt);  color: var(--accent-green);  border-color: var(--accent-green-lt); }
.info-pill.orange { background: var(--accent-orange-lt); color: var(--accent-orange); border-color: var(--accent-orange-lt); }
.info-pill.teal   { background: var(--accent-teal-lt);   color: var(--accent-teal);   border-color: var(--accent-teal-lt); }

/* ════════════════════════════════════════════
   BARRA DE EJECUCION PRESUPUESTAL
   ════════════════════════════════════════════ */
.presup-bar-wrap {
    background: var(--border);
    border-radius: 4px;
    height: 8px;
    overflow: hidden;
}
.presup-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: var(--exec-completado);
    transition: width 0.5s ease;
}
.presup-bar-fill.warn   { background: var(--exec-atrasado); }
.presup-bar-fill.danger { background: var(--exec-critico); }

/* ════════════════════════════════════════════
   BOTON CTA (Bogota Yellow)
   ════════════════════════════════════════════ */
.stApp .stButton > button[kind="primary"],
.stApp .stFormSubmitButton > button {
    background-color: var(--btn-cta-bg) !important;
    color: var(--btn-cta-fg) !important;
    border: 1px solid var(--btn-cta-border) !important;
    font-weight: 700 !important;
}
.stApp .stButton > button[kind="primary"]:hover,
.stApp .stFormSubmitButton > button:hover {
    background-color: var(--bogota-gold, #E6BC00) !important;
    border-color: var(--bogota-gold, #E6BC00) !important;
}

/* ════════════════════════════════════════════
   TIPOGRAFIA Y CONTENEDORES
   ════════════════════════════════════════════ */
.stDataFrame { border-radius: 8px; overflow: hidden; }

.stButton > button {
    font-family: 'Barlow', sans-serif;
    font-weight: 600;
    border-radius: 6px;
}

hr { border-color: var(--border); }

details summary {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.84rem;
    color: var(--text-secondary);
}

h1, h2, h3 {
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    color: var(--text-primary);
}
h3 {
    border-bottom: 2px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 1.1rem;
}

/* ════════════════════════════════════════════
   LOGIN
   ════════════════════════════════════════════ */
.login-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2.5rem 2rem;
}

/* ════════════════════════════════════════════
   EXPANDER DE REGISTROS (registros de obra)
   ════════════════════════════════════════════ */
.record-meta-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 0.75rem;
}
.record-field-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 0.5rem 1rem;
    margin-bottom: 0.75rem;
}
.record-field-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--text-muted);
    margin-bottom: 2px;
}
.record-field-value {
    font-family: 'Barlow', sans-serif;
    font-size: 0.90rem;
    font-weight: 600;
    color: var(--text-primary);
}

/* ════════════════════════════════════════════
   INDICADORES ACUMULADOS (mini-panel)
   ════════════════════════════════════════════ */
.acum-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.75rem;
    display: flex;
    flex-wrap: wrap;
    gap: 1rem 2rem;
    align-items: flex-start;
}
.acum-panel-title {
    width: 100%;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.63rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}
.acum-item { }
.acum-item-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.acum-item-value {
    font-family: 'Barlow', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
}
</style>
"""
