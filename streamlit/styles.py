"""
styles.py — CSS global de la aplicación BDO IDU-1556-2025
Paleta institucional IDU Bogotá · Modo claro y oscuro con variables CSS.
Sidebar siempre oscuro (estilo panel IDU).
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800&family=Barlow+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ════════════════════════════════════════════
   VARIABLES — MODO CLARO (por defecto)
   ════════════════════════════════════════════ */
:root {
    /* ─── Paleta IDU Bogotá ─── */
    --idu-navy:        #1a3a6e;
    --idu-navy-deep:   #0d2152;
    --idu-navy-lt:     #d6e4f7;
    --idu-teal:        #005c4e;
    --idu-teal-lt:     #ccf0ea;
    --idu-amber:       #c97a00;
    --idu-amber-lt:    #ffefd0;

    /* Fondos */
    --bg-app:          #eef1f6;
    --bg-card:         #ffffff;
    --bg-card-hover:   #f5f8ff;
    --bg-sidebar:      #0d1e3d;
    --bg-sidebar-item: rgba(255,255,255,0.06);
    --bg-inset:        #f0f3f9;

    /* Bordes */
    --border:          #d0d9e8;
    --border-strong:   #a8b8d0;

    /* Texto */
    --text-primary:    #0d1e3d;
    --text-secondary:  #2a3f6b;
    --text-muted:      #637090;
    --text-sidebar:    #c8d4e6;
    --text-sidebar-muted: #6a7d9b;

    /* Acentos semánticos */
    --accent-blue:     #1a3a6e;
    --accent-blue-lt:  #d6e4f7;
    --accent-green:    #005c4e;
    --accent-green-lt: #ccf0ea;
    --accent-red:      #aa1b1b;
    --accent-red-lt:   #fde5e5;
    --accent-orange:   #c97a00;
    --accent-orange-lt:#ffefd0;
    --accent-purple:   #5b21b6;
    --accent-purple-lt:#ede9fe;
    --accent-teal:     #0e7490;
    --accent-teal-lt:  #cff1fb;

    /* Nav */
    --nav-cat-color:    #6a7d9b;
    --nav-cat-hi-color: #60a8e8;
    --nav-active-bg:    rgba(255,255,255,0.13);
    --nav-active-border:#60a8e8;
    --nav-active-text:  #ffffff;
    --nav-idle-text:    #99b2cc;

    /* Badges de estado */
    --badge-borrador-bg:  #edf0f5; --badge-borrador-fg: #4a5e80;
    --badge-revisado-bg:  #ccf0ea; --badge-revisado-fg: #003e33;
    --badge-aprobado-bg:  #d6e4f7; --badge-aprobado-fg: #0d2152;
    --badge-devuelto-bg:  #fde5e5; --badge-devuelto-fg: #7a1010;

    /* KPI */
    --kpi-value-color:  #0d1e3d;

    /* Botones de acción */
    --btn-approve-bg:   #005c4e;
    --btn-approve-fg:   #ffffff;
    --btn-return-bg:    #aa1b1b;
    --btn-return-fg:    #ffffff;
}

/* ════════════════════════════════════════════
   VARIABLES — MODO OSCURO
   ════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
    :root {
        --idu-navy:        #3d6ec5;
        --idu-navy-deep:   #5585d8;
        --idu-navy-lt:     #162d5c;
        --idu-teal:        #00b89a;
        --idu-teal-lt:     #003d34;
        --idu-amber:       #f5a623;
        --idu-amber-lt:    #3d2800;

        --bg-app:          #0a1020;
        --bg-card:         #111827;
        --bg-card-hover:   #1a2540;
        --bg-sidebar:      #060d1a;
        --bg-sidebar-item: rgba(255,255,255,0.05);
        --bg-inset:        #0d1629;

        --border:          #1e2d4d;
        --border-strong:   #2d4070;

        --text-primary:    #dce8f8;
        --text-secondary:  #b0c4df;
        --text-muted:      #6b84a6;
        --text-sidebar:    #b0c4df;
        --text-sidebar-muted: #4d6585;

        --accent-blue:     #5585d8;
        --accent-blue-lt:  #162d5c;
        --accent-green:    #00b89a;
        --accent-green-lt: #003d34;
        --accent-red:      #f26868;
        --accent-red-lt:   #3d1010;
        --accent-orange:   #f5a623;
        --accent-orange-lt:#3d2800;
        --accent-purple:   #c4a3ff;
        --accent-purple-lt:#2d1f60;
        --accent-teal:     #38d4f5;
        --accent-teal-lt:  #0d3040;

        --nav-cat-color:    #4d6585;
        --nav-cat-hi-color: #5585d8;
        --nav-active-bg:    rgba(85,133,216,0.16);
        --nav-active-border:#5585d8;
        --nav-active-text:  #dce8f8;
        --nav-idle-text:    #6b84a6;

        --badge-borrador-bg:  #1a2540; --badge-borrador-fg: #6b84a6;
        --badge-revisado-bg:  #003d34; --badge-revisado-fg: #00b89a;
        --badge-aprobado-bg:  #162d5c; --badge-aprobado-fg: #5585d8;
        --badge-devuelto-bg:  #3d1010; --badge-devuelto-fg: #f26868;

        --kpi-value-color:  #dce8f8;

        --btn-approve-bg:   #00b89a;
        --btn-approve-fg:   #001a16;
        --btn-return-bg:    #f26868;
        --btn-return-fg:    #1a0000;
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
   SIDEBAR — siempre oscuro (estilo panel IDU)
   ════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar) !important;
    border-right: 1px solid rgba(85,133,216,0.12);
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
    background: rgba(85,133,216,0.15) !important;
    color: #ffffff !important;
    border-color: rgba(85,133,216,0.3) !important;
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

/* Categoría normal */
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

/* Categoría destacada */
.nav-cat-hi {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.60rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--nav-cat-hi-color) !important;
    padding: 0.65rem 0 0.2rem 0;
    border-top: 1px solid rgba(85,133,216,0.18);
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
/* Tags del multiselect */
.stMultiSelect [data-baseweb="tag"] {
    background-color: var(--accent-blue-lt) !important;
    color: var(--accent-blue) !important;
    font-weight: 700 !important;
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
    background: linear-gradient(135deg, var(--idu-navy-deep) 0%, var(--idu-navy) 100%);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
    color: #fff;
    position: relative;
    overflow: hidden;
}
/* watermark removido */
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
   PANEL DE APROBACIÓN
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
   TABLA DE SEGUIMIENTO (adiciones / prórrogas)
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
   INFO PILLS (indicadores pequeños en filas)
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
   BARRA DE EJECUCIÓN PRESUPUESTAL
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
    background: var(--accent-green);
    transition: width 0.5s ease;
}
.presup-bar-fill.warn   { background: var(--accent-orange); }
.presup-bar-fill.danger { background: var(--accent-red); }

/* ════════════════════════════════════════════
   TIPOGRAFÍA Y CONTENEDORES
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
