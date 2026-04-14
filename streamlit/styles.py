"""
styles.py — CSS global de la aplicacion BDO IDU-1556-2025
Paleta institucional Bogota / IDU · Modo claro y oscuro con variables CSS.
Sidebar siempre oscuro (estilo panel IDU).
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800&family=Barlow:wght@400;500;600;700;800&family=Barlow+Condensed:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ════════════════════════════════════════════
   VARIABLES — MODO CLARO (por defecto)
   Guía de Identidad Visual IDU 2025
   ════════════════════════════════════════════ */
:root {
    /* --- Identidad Central IDU --- */
    --idu-blue:        #00A6E1;   /* Azul IDU primario — logo, titulos, tabs activas */
    --idu-blue-dark:   #0076B0;   /* Azul Oscuro — cabeceras de tabla, fondos panel */
    --idu-blue-lt:     #d0eef9;   /* Azul IDU claro — fondos de badge */
    --idu-red:         #ED1C24;   /* Rojo Bogota — botones de accion, alertas */
    --idu-red-lt:      #fde8e9;   /* Rojo claro — fondos de alerta */
    --idu-yellow:      #FFC425;   /* Amarillo Estelar — advertencias, iconos soporte */
    --idu-yellow-lt:   #fff5d6;   /* Amarillo claro */
    --idu-green:       #198754;   /* Verde cumplido — semaforo */
    --idu-green-lt:    #d1f2dc;

    /* --- Backward-compat aliases --- */
    --bogota-blue-deep:  #0076B0;
    --bogota-blue-active:#00A6E1;
    --bogota-yellow:     #FFC425;
    --bogota-gold:       #e6ae20;
    --idu-navy:        #00A6E1;
    --idu-navy-deep:   #0076B0;
    --idu-navy-lt:     #d0eef9;
    --idu-teal:        #198754;
    --idu-teal-lt:     #d1f2dc;
    --idu-amber:       #FFC425;
    --idu-amber-lt:    #fff5d6;

    /* Fondos */
    --bg-app:          #EDF1F6;   /* Gris Neutro — fondo general */
    --bg-card:         #FFFFFF;   /* Blanco puro — tarjetas de contenido */
    --bg-card-hover:   #f0f7fc;
    --bg-sidebar:      #0076B0;   /* Azul Oscuro — sidebar institucional */
    --bg-sidebar-item: rgba(255,255,255,0.08);
    --bg-inset:        #EDF1F6;

    /* Bordes */
    --border:          #D8E3ED;
    --border-strong:   #B0BEC5;

    /* Texto */
    --text-primary:    #4D4D4D;   /* Gris Texto — lectura larga */
    --text-secondary:  #4D4D4D;
    --text-muted:      #7A8A99;
    --text-sidebar:    #FFFFFF;
    --text-sidebar-muted: #c8dff0;

    /* Acentos semanticos — mapeados a paleta IDU */
    --accent-blue:     #00A6E1;
    --accent-blue-lt:  #d0eef9;
    --accent-green:    #198754;
    --accent-green-lt: #d1f2dc;
    --accent-red:      #ED1C24;
    --accent-red-lt:   #fde8e9;
    --accent-orange:   #FFC425;
    --accent-orange-lt:#fff5d6;
    --accent-purple:   #6f42c1;
    --accent-purple-lt:#e8dcf8;
    --accent-teal:     #0076B0;
    --accent-teal-lt:  #cce7f5;

    /* Semáforo de ejecución */
    --exec-completado: #198754;   /* Verde — cumplido */
    --exec-progreso:   #FFC425;   /* Amarillo Estelar — en proceso */
    --exec-atrasado:   #FFC425;
    --exec-critico:    #ED1C24;   /* Rojo Bogotá — retraso/alerta */
    --exec-planeacion: #B0BEC5;

    /* Nav */
    --nav-cat-color:    #c8dff0;
    --nav-cat-hi-color: #FFC425;
    --nav-active-bg:    rgba(0,166,225,0.15);
    --nav-active-border:#00A6E1;
    --nav-active-text:  #ffffff;
    --nav-idle-text:    #c8dff0;

    /* Badges de estado */
    --badge-borrador-bg:  #EDF1F6; --badge-borrador-fg: #4D4D4D;
    --badge-revisado-bg:  #d0eef9; --badge-revisado-fg: #003d61;  /* oscurecido: 8:1 vs #d0eef9 */
    --badge-aprobado-bg:  #d1f2dc; --badge-aprobado-fg: #0f5132;
    --badge-devuelto-bg:  #fde8e9; --badge-devuelto-fg: #ED1C24;
    --badge-amarillo-bg:  #FFC425; --badge-amarillo-fg: #3d2800;  /* Amarillo Estelar IDU */

    /* KPI */
    --kpi-value-color:  #00A6E1;  /* Cifras grandes en Azul IDU */

    /* Botones */
    --btn-approve-bg:   #198754;
    --btn-approve-fg:   #ffffff;
    --btn-return-bg:    #ED1C24;
    --btn-return-fg:    #ffffff;

    /* CTA principal (guardar, generar PDF) → Rojo Bogotá */
    --btn-cta-bg:       #ED1C24;
    --btn-cta-fg:       #ffffff;
    --btn-cta-border:   #c01019;

    /* CTA filtros / navegación → Azul IDU */
    --btn-filter-bg:    #00A6E1;
    --btn-filter-fg:    #ffffff;
    --btn-filter-border:#0090c3;
}

/* ════════════════════════════════════════════
   VARIABLES — MODO OSCURO
   Paleta institucional IDU adaptada al oscuro
   Superficies por elevación, contraste AA
   ════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
    :root {
        /* IDU en oscuro — versiones encendidas para buen contraste */
        --idu-blue:        #33B5E5;   /* Azul IDU suavizado — titulos, tabs activas */
        --idu-blue-dark:   #004B6B;   /* Cabeceras de tabla en oscuro */
        --idu-blue-lt:     #0d2f3f;
        --idu-red:         #FF5252;   /* Rojo Bogotá vibrante — botones, alertas */
        --idu-red-lt:      #3d1010;
        --idu-yellow:      #FFD54F;   /* Amarillo Estelar — advertencias */
        --idu-yellow-lt:   #3d2800;
        --idu-green:       #3fb950;
        --idu-green-lt:    #0d2818;

        /* Backward-compat aliases */
        --bogota-blue-deep:  #004B6B;
        --bogota-blue-active:#33B5E5;
        --bogota-yellow:     #FFD54F;
        --bogota-gold:       #e6ae20;
        --idu-navy:        #33B5E5;
        --idu-navy-deep:   #004B6B;
        --idu-navy-lt:     #0d2f3f;
        --idu-teal:        #3fb950;
        --idu-teal-lt:     #0d2818;
        --idu-amber:       #FFD54F;
        --idu-amber-lt:    #3d2800;

        /* Superficies por elevación */
        --bg-app:          #121212;   /* Fondo aplicación */
        --bg-card:         #1E1E1E;   /* Tarjetas/paneles */
        --bg-card-hover:   #252525;
        --bg-sidebar:      #0d1a22;   /* Panel lateral oscuro */
        --bg-sidebar-item: rgba(255,255,255,0.05);
        --bg-inset:        #1E1E1E;

        /* Bordes sutiles */
        --border:          #333333;
        --border-strong:   #444444;

        /* Texto sin deslumbramiento */
        --text-primary:    #E0E0E0;   /* Blanco roto — texto principal */
        --text-secondary:  #A0A0A0;   /* Gris medio — etiquetas, unidades */
        --text-muted:      #A0A0A0;
        --text-sidebar:    #E0E0E0;
        --text-sidebar-muted: #A0A0A0;

        /* Acentos oscuros */
        --accent-blue:     #33B5E5;
        --accent-blue-lt:  #0d2f3f;
        --accent-green:    #3fb950;
        --accent-green-lt: #0d2818;
        --accent-red:      #FF5252;
        --accent-red-lt:   #3d1010;
        --accent-orange:   #FFD54F;
        --accent-orange-lt:#3d2800;
        --accent-purple:   #bc8cff;
        --accent-purple-lt:#2d1f60;
        --accent-teal:     #33B5E5;
        --accent-teal-lt:  #0d2f3f;

        /* Semáforo oscuro */
        --exec-completado: #3fb950;
        --exec-progreso:   #FFD54F;
        --exec-atrasado:   #FFD54F;
        --exec-critico:    #FF5252;
        --exec-planeacion: #444444;

        /* Nav */
        --nav-cat-color:    #A0A0A0;
        --nav-cat-hi-color: #FFD54F;
        --nav-active-bg:    rgba(51,181,229,0.12);
        --nav-active-border:#33B5E5;
        --nav-active-text:  #E0E0E0;
        --nav-idle-text:    #A0A0A0;

        /* Badges */
        --badge-borrador-bg:  #252525; --badge-borrador-fg: #A0A0A0;
        --badge-revisado-bg:  #0d2f3f; --badge-revisado-fg: #7dd4f5;  /* claro sobre fondo oscuro */
        --badge-aprobado-bg:  #0d2818; --badge-aprobado-fg: #3fb950;
        --badge-devuelto-bg:  #3d1010; --badge-devuelto-fg: #FF5252;
        --badge-amarillo-bg:  #3d2800; --badge-amarillo-fg: #FFD54F;

        --kpi-value-color:  #33B5E5;

        --btn-approve-bg:   #3fb950;
        --btn-approve-fg:   #0d1117;
        --btn-return-bg:    #FF5252;
        --btn-return-fg:    #0d1117;

        /* CTA principal oscuro → Rojo Bogotá */
        --btn-cta-bg:       #FF5252;
        --btn-cta-fg:       #ffffff;
        --btn-cta-border:   #e03030;

        /* CTA filtros oscuro → Azul IDU */
        --btn-filter-bg:    #33B5E5;
        --btn-filter-fg:    #0d1117;
        --btn-filter-border:#2299c5;
    }
}

/* ════════════════════════════════════════════
   BASE
   ════════════════════════════════════════════ */
html, body, [class*="css"] {
    font-family: 'Barlow', 'IBM Plex Sans', sans-serif;
    color: var(--text-primary);
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
    background: rgba(0,166,225,0.25) !important;
    color: #ffffff !important;
    border-color: rgba(0,166,225,0.45) !important;
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
.kpi-card.accent-orange::before { background: #FFC425; }  /* Amarillo Estelar IDU */
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
    display: flex;
    align-items: center;
    gap: 6px;
}
/* Bolita amarilla IDU antes del título del formulario */
.filter-form-title::before {
    content: '';
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #FFC425;
    flex-shrink: 0;
}

/* ════════════════════════════════════════════
   INPUTS — base legible en todos los estados
   Problema raíz: color-scheme:dark del OS hace
   que el browser pinte los inputs en oscuro aun
   cuando nuestro CSS dice background:#fff.
   Solución: forzar color-scheme:light + selectores
   [data-testid] que superan la especificidad de
   Streamlit. Se aplica a TODAS las páginas.
   ════════════════════════════════════════════ */

/* ── Base: todos los inputs siempre en claro ──── */
[data-testid="stTextInput"]   input,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"]   input,
[data-testid="stTimeInput"]   input,
[data-testid="stTextArea"]    textarea {
    color-scheme: light !important;   /* evita que el OS oscuro tire el fondo negro */
    background-color: #ffffff !important;
    color: #4D4D4D !important;
    border-color: #D8E3ED !important;
    transition: background-color 0.18s, border-color 0.18s, box-shadow 0.18s;
}

/* ── Placeholder legible ─────────────────────── */
[data-testid="stTextInput"]   input::placeholder,
[data-testid="stNumberInput"] input::placeholder,
[data-testid="stDateInput"]   input::placeholder,
[data-testid="stTextArea"]    textarea::placeholder {
    color: #9aabb8 !important;
    opacity: 1 !important;
}

/* ── Focus: borde Azul IDU + halo sutil ───────── */
[data-testid="stTextInput"]   input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stDateInput"]   input:focus,
[data-testid="stTextArea"]    textarea:focus {
    background-color: #f0f8fd !important;
    border-color: #00A6E1 !important;
    box-shadow: 0 0 0 2px rgba(0,166,225,0.18) !important;
    outline: none !important;
}

/* ── Selectbox base ───────────────────────────── */
[data-testid="stSelectbox"]   [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div {
    color-scheme: light !important;
    background-color: #ffffff !important;
    color: #4D4D4D !important;
    border-color: #D8E3ED !important;
    transition: background-color 0.18s, border-color 0.18s, box-shadow 0.18s;
}

/* ── Selectbox abierto / con foco ─────────────── */
[data-testid="stSelectbox"]   [data-baseweb="select"] > div[aria-expanded="true"],
[data-testid="stSelectbox"]   [data-baseweb="select"]:focus-within > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div[aria-expanded="true"],
[data-testid="stMultiSelect"] [data-baseweb="select"]:focus-within > div {
    background-color: #f0f8fd !important;
    border-color: #00A6E1 !important;
    box-shadow: 0 0 0 2px rgba(0,166,225,0.18) !important;
}

/* ── Texto dentro del trigger del selectbox ────── */
[data-testid="stSelectbox"]   [data-baseweb="select"] span,
[data-testid="stSelectbox"]   [data-baseweb="select"] div[class*="placeholder"],
[data-testid="stMultiSelect"] [data-baseweb="select"] span {
    color: #4D4D4D !important;
}

/* ── Dropdown (lista de opciones) ─────────────── */
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="menu"] {
    background-color: #ffffff !important;
    border: 1px solid #D8E3ED !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] li,
[data-baseweb="menu"] [role="option"] {
    color: #4D4D4D !important;
    background-color: transparent !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.88rem !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [role="option"]:hover {
    background-color: #d0eef9 !important;
    color: #004a7c !important;
}
[data-baseweb="menu"] [aria-selected="true"] {
    background-color: #00A6E1 !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* ── Multiselect tags (chips) ─────────────────── */
[data-testid="stMultiSelect"] [data-baseweb="tag"] {
    background-color: #d0eef9 !important;
    color: #004a7c !important;
    font-weight: 700 !important;
    border: 1px solid rgba(0,74,124,0.2) !important;
}
[data-testid="stMultiSelect"] [data-baseweb="select"]:has([data-baseweb="tag"]) > div {
    background-color: #f0f8fd !important;
    border-color: #00A6E1 !important;
}

/* ── Checkbox ─────────────────────────────────── */
[data-testid="stCheckbox"] label span:first-child {
    border-color: #D8E3ED !important;
}

/* ════════════════════════════════════════════
   SELECCIÓN DE TEXTO — Amarillo Estelar IDU
   Texto seleccionado con Ctrl+A o clic-drag
   queda destacado en amarillo institucional.
   ════════════════════════════════════════════ */
.stTextInput input::selection,
.stTextArea textarea::selection,
.stNumberInput input::selection {
    background-color: #FFC425 !important;
    color: #1a1000 !important;
}
/* Chips/tags del multiselect — texto dentro del tag */
.stMultiSelect [data-baseweb="tag"] span {
    color: inherit !important;
}
/* Dropdown option resaltado (hover en desplegable) */
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="menu"] [aria-selected="true"] {
    background-color: var(--idu-blue-lt, #d0eef9) !important;
    color: #004a7c !important;
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
.sb-blue   { background: var(--idu-blue-lt, #d0eef9);   color: #004a7c;  /* ratio ≈ 7:1 */ }
.sb-green  { background: var(--accent-green-lt);         color: var(--accent-green);           }
.sb-red    { background: var(--idu-red-lt, #fde8e9);     color: var(--idu-red, #ED1C24);       }
.sb-orange { background: var(--idu-yellow-lt, #fff5d6);  color: #8a6200;                       }
.sb-yellow { background: #FFC425;                        color: #3d2800;  /* Amarillo Estelar — ratio ≈ 9:1 */ }
.sb-purple { background: var(--accent-purple-lt);        color: var(--accent-purple);           }
.sb-teal   { background: var(--accent-teal-lt);          color: #003d61;  /* ratio ≈ 8:1 */ }

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
.badge-borrador  { background: var(--badge-borrador-bg);  color: var(--badge-borrador-fg);  }
.badge-revisado  { background: var(--badge-revisado-bg);  color: var(--badge-revisado-fg);  }
.badge-aprobado  { background: var(--badge-aprobado-bg);  color: var(--badge-aprobado-fg);  }
.badge-devuelto  { background: var(--badge-devuelto-bg);  color: var(--badge-devuelto-fg);  }
.badge-amarillo  { background: var(--badge-amarillo-bg, #FFC425); color: var(--badge-amarillo-fg, #3d2800); }

/* ════════════════════════════════════════════
   CONTRATO — HEADER Y FICHAS
   ════════════════════════════════════════════ */
.contract-header {
    background: linear-gradient(135deg, #00A6E1 0%, #0076B0 100%);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
    color: #fff;
    position: relative;
    overflow: hidden;
    /* Franja Amarillo Estelar IDU en el borde inferior — acento institucional */
    border-bottom: 4px solid #FFC425;
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
   BOTONES CTA — Identidad Visual IDU
   Acciones (guardar / PDF): Rojo Bogotá
   Filtros / navegación:     Azul IDU
   ════════════════════════════════════════════ */
/* Botones de acción principal (type="primary") → Rojo Bogotá */
.stApp .stButton > button[kind="primary"] {
    background-color: var(--btn-cta-bg) !important;
    color: var(--btn-cta-fg) !important;
    border: 1px solid var(--btn-cta-border) !important;
    font-weight: 700 !important;
    font-family: 'Barlow', sans-serif !important;
}
.stApp .stButton > button[kind="primary"]:hover {
    background-color: #c01019 !important;
    border-color: #a00d14 !important;
}
/* Botones de formulario de filtros → Azul IDU */
.stApp .stFormSubmitButton > button {
    background-color: var(--btn-filter-bg) !important;
    color: var(--btn-filter-fg) !important;
    border: 1px solid var(--btn-filter-border) !important;
    font-weight: 700 !important;
    font-family: 'Barlow', sans-serif !important;
}
.stApp .stFormSubmitButton > button:hover {
    background-color: #0090c3 !important;
    border-color: #007aaa !important;
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
    font-family: 'Montserrat', 'Barlow', sans-serif;
    font-weight: 700;
    color: var(--idu-blue);   /* Azul IDU para todos los títulos */
}
h3 {
    border-bottom: 2px solid var(--idu-blue);
    padding-bottom: 0.5rem;
    margin-bottom: 1.1rem;
}

/* Tabs — Activa: Azul IDU / Inactiva: Gris Neutro */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Barlow', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border-radius: 6px 6px 0 0 !important;
    background: var(--bg-inset) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-bottom: none !important;
    padding: 0.45rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: var(--idu-blue) !important;
    color: #ffffff !important;
    border-color: var(--idu-blue) !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
@media (prefers-color-scheme: dark) {
    .stTabs [data-baseweb="tab"] {
        background: #252525 !important;
        color: var(--text-secondary) !important;
    }
    .stTabs [aria-selected="true"] {
        background: var(--idu-blue) !important;
        color: #0d1117 !important;
    }
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

/* ════════════════════════════════════════════
   TEMA — SINCRONIZADO POR JS (data-bdo-theme)
   Anula @media prefers-color-scheme cuando el
   usuario cambia el tema dentro de Streamlit,
   independiente del modo del sistema operativo.
   ════════════════════════════════════════════ */

/* Forzar modo claro aunque el OS sea oscuro */
html[data-bdo-theme="light"] {
    --idu-blue:        #00A6E1;
    --idu-blue-dark:   #0076B0;
    --idu-blue-lt:     #d0eef9;
    --idu-red:         #ED1C24;
    --idu-red-lt:      #fde8e9;
    --idu-yellow:      #FFC425;
    --idu-yellow-lt:   #fff5d6;
    --idu-green:       #198754;
    --idu-green-lt:    #d1f2dc;
    --bogota-blue-deep:  #0076B0;
    --bogota-blue-active:#00A6E1;
    --bogota-yellow:     #FFC425;
    --bogota-gold:       #e6ae20;
    --idu-navy:        #00A6E1;
    --idu-navy-deep:   #0076B0;
    --idu-navy-lt:     #d0eef9;
    --idu-teal:        #198754;
    --idu-teal-lt:     #d1f2dc;
    --idu-amber:       #FFC425;
    --idu-amber-lt:    #fff5d6;
    --bg-app:          #EDF1F6;
    --bg-card:         #FFFFFF;
    --bg-card-hover:   #f0f7fc;
    --bg-sidebar:      #0076B0;
    --bg-sidebar-item: rgba(255,255,255,0.08);
    --bg-inset:        #EDF1F6;
    --border:          #D8E3ED;
    --border-strong:   #B0BEC5;
    --text-primary:    #4D4D4D;
    --text-secondary:  #4D4D4D;
    --text-muted:      #7A8A99;
    --text-sidebar:    #FFFFFF;
    --text-sidebar-muted: #c8dff0;
    --accent-blue:     #00A6E1;
    --accent-blue-lt:  #d0eef9;
    --accent-green:    #198754;
    --accent-green-lt: #d1f2dc;
    --accent-red:      #ED1C24;
    --accent-red-lt:   #fde8e9;
    --accent-orange:   #FFC425;
    --accent-orange-lt:#fff5d6;
    --accent-purple:   #6f42c1;
    --accent-purple-lt:#e8dcf8;
    --accent-teal:     #0076B0;
    --accent-teal-lt:  #cce7f5;
    --exec-completado: #198754;
    --exec-progreso:   #FFC425;
    --exec-atrasado:   #FFC425;
    --exec-critico:    #ED1C24;
    --exec-planeacion: #B0BEC5;
    --nav-cat-color:    #c8dff0;
    --nav-cat-hi-color: #FFC425;
    --nav-active-bg:    rgba(0,166,225,0.15);
    --nav-active-border:#00A6E1;
    --nav-active-text:  #ffffff;
    --nav-idle-text:    #c8dff0;
    --badge-borrador-bg:  #EDF1F6; --badge-borrador-fg: #4D4D4D;
    --badge-revisado-bg:  #d0eef9; --badge-revisado-fg: #003d61;
    --badge-aprobado-bg:  #d1f2dc; --badge-aprobado-fg: #0f5132;
    --badge-devuelto-bg:  #fde8e9; --badge-devuelto-fg: #ED1C24;
    --badge-amarillo-bg:  #FFC425; --badge-amarillo-fg: #3d2800;
    --kpi-value-color:  #00A6E1;
    --btn-approve-bg:   #198754;
    --btn-approve-fg:   #ffffff;
    --btn-return-bg:    #ED1C24;
    --btn-return-fg:    #ffffff;
    --btn-cta-bg:       #ED1C24;
    --btn-cta-fg:       #ffffff;
    --btn-cta-border:   #c01019;
    --btn-filter-bg:    #00A6E1;
    --btn-filter-fg:    #ffffff;
    --btn-filter-border:#0090c3;
}

/* Forzar modo oscuro aunque el OS sea claro */
html[data-bdo-theme="dark"] {
    --idu-blue:        #33B5E5;
    --idu-blue-dark:   #004B6B;
    --idu-blue-lt:     #0d2f3f;
    --idu-red:         #FF5252;
    --idu-red-lt:      #3d1010;
    --idu-yellow:      #FFD54F;
    --idu-yellow-lt:   #3d2800;
    --idu-green:       #3fb950;
    --idu-green-lt:    #0d2818;
    --bogota-blue-deep:  #004B6B;
    --bogota-blue-active:#33B5E5;
    --bogota-yellow:     #FFD54F;
    --bogota-gold:       #e6ae20;
    --idu-navy:        #33B5E5;
    --idu-navy-deep:   #004B6B;
    --idu-navy-lt:     #0d2f3f;
    --idu-teal:        #3fb950;
    --idu-teal-lt:     #0d2818;
    --idu-amber:       #FFD54F;
    --idu-amber-lt:    #3d2800;
    --bg-app:          #121212;
    --bg-card:         #1E1E1E;
    --bg-card-hover:   #252525;
    --bg-sidebar:      #0d1a22;
    --bg-sidebar-item: rgba(255,255,255,0.05);
    --bg-inset:        #1E1E1E;
    --border:          #333333;
    --border-strong:   #444444;
    --text-primary:    #E0E0E0;
    --text-secondary:  #A0A0A0;
    --text-muted:      #A0A0A0;
    --text-sidebar:    #E0E0E0;
    --text-sidebar-muted: #A0A0A0;
    --accent-blue:     #33B5E5;
    --accent-blue-lt:  #0d2f3f;
    --accent-green:    #3fb950;
    --accent-green-lt: #0d2818;
    --accent-red:      #FF5252;
    --accent-red-lt:   #3d1010;
    --accent-orange:   #FFD54F;
    --accent-orange-lt:#3d2800;
    --accent-purple:   #bc8cff;
    --accent-purple-lt:#2d1f60;
    --accent-teal:     #33B5E5;
    --accent-teal-lt:  #0d2f3f;
    --exec-completado: #3fb950;
    --exec-progreso:   #FFD54F;
    --exec-atrasado:   #FFD54F;
    --exec-critico:    #FF5252;
    --exec-planeacion: #444444;
    --nav-cat-color:    #A0A0A0;
    --nav-cat-hi-color: #FFD54F;
    --nav-active-bg:    rgba(51,181,229,0.12);
    --nav-active-border:#33B5E5;
    --nav-active-text:  #E0E0E0;
    --nav-idle-text:    #A0A0A0;
    --badge-borrador-bg:  #252525; --badge-borrador-fg: #A0A0A0;
    --badge-revisado-bg:  #0d2f3f; --badge-revisado-fg: #7dd4f5;  /* claro sobre oscuro */
    --badge-aprobado-bg:  #0d2818; --badge-aprobado-fg: #3fb950;
    --badge-devuelto-bg:  #3d1010; --badge-devuelto-fg: #FF5252;
    --badge-amarillo-bg:  #3d2800; --badge-amarillo-fg: #FFD54F;  /* amarillo sobre oscuro */
    --kpi-value-color:  #33B5E5;
    --btn-approve-bg:   #3fb950;
    --btn-approve-fg:   #0d1117;
    --btn-return-bg:    #FF5252;
    --btn-return-fg:    #0d1117;
    --btn-cta-bg:       #FF5252;
    --btn-cta-fg:       #ffffff;
    --btn-cta-border:   #e03030;
    --btn-filter-bg:    #33B5E5;
    --btn-filter-fg:    #0d1117;
    --btn-filter-border:#2299c5;
}

/* Tabs dark override (también por data-bdo-theme) */
html[data-bdo-theme="dark"] .stTabs [data-baseweb="tab"] {
    background: #252525 !important;
    color: #A0A0A0 !important;
}
html[data-bdo-theme="dark"] .stTabs [aria-selected="true"] {
    background: #33B5E5 !important;
    color: #0d1117 !important;
}
html[data-bdo-theme="light"] .stTabs [data-baseweb="tab"] {
    background: var(--bg-inset) !important;
    color: var(--text-primary) !important;
}
html[data-bdo-theme="light"] .stTabs [aria-selected="true"] {
    background: #00A6E1 !important;
    color: #ffffff !important;
}
</style>
"""

# ── Overrides de variables CSS para inyección desde Python ──────────────────
# app.py usa st.get_option("theme.base") para detectar el tema activo y
# luego inyecta el bloque correspondiente DESPUÉS del CSS principal.
# Al aparecer más tarde en el documento, el :root posterior gana en cascada
# sobre el @media prefers-color-scheme del bloque principal, sincronizando
# el CSS personalizado con el tema real de Streamlit (incluido el toggle UI).

_LIGHT_ROOT_VARS = """
    --idu-blue:#00A6E1; --idu-blue-dark:#0076B0; --idu-blue-lt:#d0eef9;
    --idu-red:#ED1C24; --idu-red-lt:#fde8e9;
    --idu-yellow:#FFC425; --idu-yellow-lt:#fff5d6;
    --idu-green:#198754; --idu-green-lt:#d1f2dc;
    --bogota-blue-deep:#0076B0; --bogota-blue-active:#00A6E1;
    --bogota-yellow:#FFC425; --bogota-gold:#e6ae20;
    --idu-navy:#00A6E1; --idu-navy-deep:#0076B0; --idu-navy-lt:#d0eef9;
    --idu-teal:#198754; --idu-teal-lt:#d1f2dc;
    --idu-amber:#FFC425; --idu-amber-lt:#fff5d6;
    --bg-app:#EDF1F6; --bg-card:#FFFFFF; --bg-card-hover:#f0f7fc;
    --bg-sidebar:#0076B0; --bg-sidebar-item:rgba(255,255,255,0.08); --bg-inset:#EDF1F6;
    --border:#D8E3ED; --border-strong:#B0BEC5;
    --text-primary:#4D4D4D; --text-secondary:#4D4D4D; --text-muted:#7A8A99;
    --text-sidebar:#FFFFFF; --text-sidebar-muted:#c8dff0;
    --accent-blue:#00A6E1; --accent-blue-lt:#d0eef9;
    --accent-green:#198754; --accent-green-lt:#d1f2dc;
    --accent-red:#ED1C24; --accent-red-lt:#fde8e9;
    --accent-orange:#FFC425; --accent-orange-lt:#fff5d6;
    --accent-purple:#6f42c1; --accent-purple-lt:#e8dcf8;
    --accent-teal:#0076B0; --accent-teal-lt:#cce7f5;
    --exec-completado:#198754; --exec-progreso:#FFC425;
    --exec-atrasado:#FFC425; --exec-critico:#ED1C24; --exec-planeacion:#B0BEC5;
    --nav-cat-color:#c8dff0; --nav-cat-hi-color:#FFC425;
    --nav-active-bg:rgba(0,166,225,0.15); --nav-active-border:#00A6E1;
    --nav-active-text:#ffffff; --nav-idle-text:#c8dff0;
    --badge-borrador-bg:#EDF1F6; --badge-borrador-fg:#4D4D4D;
    --badge-revisado-bg:#d0eef9; --badge-revisado-fg:#003d61;
    --badge-aprobado-bg:#d1f2dc; --badge-aprobado-fg:#0f5132;
    --badge-devuelto-bg:#fde8e9; --badge-devuelto-fg:#ED1C24;
    --badge-amarillo-bg:#FFC425; --badge-amarillo-fg:#3d2800;
    --kpi-value-color:#00A6E1;
    --btn-approve-bg:#198754; --btn-approve-fg:#ffffff;
    --btn-return-bg:#ED1C24; --btn-return-fg:#ffffff;
    --btn-cta-bg:#ED1C24; --btn-cta-fg:#ffffff; --btn-cta-border:#c01019;
    --btn-filter-bg:#00A6E1; --btn-filter-fg:#ffffff; --btn-filter-border:#0090c3;
"""

_DARK_ROOT_VARS = """
    --idu-blue:#33B5E5; --idu-blue-dark:#004B6B; --idu-blue-lt:#0d2f3f;
    --idu-red:#FF5252; --idu-red-lt:#3d1010;
    --idu-yellow:#FFD54F; --idu-yellow-lt:#3d2800;
    --idu-green:#3fb950; --idu-green-lt:#0d2818;
    --bogota-blue-deep:#004B6B; --bogota-blue-active:#33B5E5;
    --bogota-yellow:#FFD54F; --bogota-gold:#e6ae20;
    --idu-navy:#33B5E5; --idu-navy-deep:#004B6B; --idu-navy-lt:#0d2f3f;
    --idu-teal:#3fb950; --idu-teal-lt:#0d2818;
    --idu-amber:#FFD54F; --idu-amber-lt:#3d2800;
    --bg-app:#121212; --bg-card:#1E1E1E; --bg-card-hover:#252525;
    --bg-sidebar:#0d1a22; --bg-sidebar-item:rgba(255,255,255,0.05); --bg-inset:#1E1E1E;
    --border:#333333; --border-strong:#444444;
    --text-primary:#E0E0E0; --text-secondary:#A0A0A0; --text-muted:#A0A0A0;
    --text-sidebar:#E0E0E0; --text-sidebar-muted:#A0A0A0;
    --accent-blue:#33B5E5; --accent-blue-lt:#0d2f3f;
    --accent-green:#3fb950; --accent-green-lt:#0d2818;
    --accent-red:#FF5252; --accent-red-lt:#3d1010;
    --accent-orange:#FFD54F; --accent-orange-lt:#3d2800;
    --accent-purple:#bc8cff; --accent-purple-lt:#2d1f60;
    --accent-teal:#33B5E5; --accent-teal-lt:#0d2f3f;
    --exec-completado:#3fb950; --exec-progreso:#FFD54F;
    --exec-atrasado:#FFD54F; --exec-critico:#FF5252; --exec-planeacion:#444444;
    --nav-cat-color:#A0A0A0; --nav-cat-hi-color:#FFD54F;
    --nav-active-bg:rgba(51,181,229,0.12); --nav-active-border:#33B5E5;
    --nav-active-text:#E0E0E0; --nav-idle-text:#A0A0A0;
    --badge-borrador-bg:#252525; --badge-borrador-fg:#A0A0A0;
    --badge-revisado-bg:#0d2f3f; --badge-revisado-fg:#7dd4f5;
    --badge-aprobado-bg:#0d2818; --badge-aprobado-fg:#3fb950;
    --badge-devuelto-bg:#3d1010; --badge-devuelto-fg:#FF5252;
    --badge-amarillo-bg:#3d2800; --badge-amarillo-fg:#FFD54F;
    --kpi-value-color:#33B5E5;
    --btn-approve-bg:#3fb950; --btn-approve-fg:#0d1117;
    --btn-return-bg:#FF5252; --btn-return-fg:#0d1117;
    --btn-cta-bg:#FF5252; --btn-cta-fg:#ffffff; --btn-cta-border:#e03030;
    --btn-filter-bg:#33B5E5; --btn-filter-fg:#0d1117; --btn-filter-border:#2299c5;
"""

# Bloques completos listos para inyectar con st.markdown(unsafe_allow_html=True).
# Al inyectarse DESPUÉS del CSS principal, la regla :root posterior gana
# sobre @media prefers-color-scheme en cascada — sin necesidad de JS.
CSS_LIGHT_OVERRIDE = f"<style>:root{{{_LIGHT_ROOT_VARS}}}</style>"
CSS_DARK_OVERRIDE  = f"<style>:root{{{_DARK_ROOT_VARS}}}</style>"

# THEME_SYNC_JS conservado por compatibilidad — no se usa en Streamlit Cloud
# porque los iframes de st.components.v1.html() tienen window.parent bloqueado.
THEME_SYNC_JS = ""
