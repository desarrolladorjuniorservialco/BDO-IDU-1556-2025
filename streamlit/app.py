"""
app.py  ·  BDO IDU-1556-2025
Bitácora Digital de Obra — Contrato IDU-1556-2025 Grupo 4
"""

import os, math
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import datetime, date, timedelta

# ══════════════════════════════════════════════════════════════
# CONFIG PÁGINA
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="BDO · IDU-1556-2025",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── Variables de color: modo claro por defecto ── */
:root {
    --bg-app:        #f5f6f8;
    --bg-card:       #ffffff;
    --bg-sidebar:    #f0f2f5;
    --border:        #dde1e7;
    --border-strong: #c4c9d4;
    --text-primary:  #1a1d23;
    --text-secondary:#4a5568;
    --text-muted:    #718096;
    --accent-blue:   #1a56db;
    --accent-green:  #1a7a3f;
    --accent-warn:   #92650a;
    --accent-danger: #c0392b;
    --badge-borrador-bg:  #edf2f7; --badge-borrador-fg: #4a5568;
    --badge-revisado-bg:  #e6f4ec; --badge-revisado-fg: #1a7a3f;
    --badge-aprobado-bg:  #e8eeff; --badge-aprobado-fg: #1a56db;
    --badge-devuelto-bg:  #fce8e8; --badge-devuelto-fg: #c0392b;
    --nav-highlight-bg:   #e8eeff;
    --nav-highlight-fg:   #1a56db;
    --nav-active-bg:      #e2e8f0;
    --kpi-value-color:    #1a1d23;
}

/* ── Variables de color: modo oscuro ── */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-app:        #0d1117;
        --bg-card:       #161b22;
        --bg-sidebar:    #0a0e16;
        --border:        #21262d;
        --border-strong: #30363d;
        --text-primary:  #e6edf3;
        --text-secondary:#c9d1d9;
        --text-muted:    #8b949e;
        --accent-blue:   #388bfd;
        --accent-green:  #3fb950;
        --accent-warn:   #d29922;
        --accent-danger: #f85149;
        --badge-borrador-bg:  #21262d; --badge-borrador-fg: #8b949e;
        --badge-revisado-bg:  #1f3d2b; --badge-revisado-fg: #3fb950;
        --badge-aprobado-bg:  #1a3255; --badge-aprobado-fg: #388bfd;
        --badge-devuelto-bg:  #3d1e1e; --badge-devuelto-fg: #f85149;
        --nav-highlight-bg:   #1a3255;
        --nav-highlight-fg:   #388bfd;
        --nav-active-bg:      #1c2333;
        --kpi-value-color:    #e6edf3;
    }
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Fondo app ── */
.stApp {
    background: var(--bg-app);
    color: var(--text-primary);
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label {
    color: var(--text-muted) !important;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    text-transform: none !important;
    font-size: 0.88rem;
    letter-spacing: 0;
    color: var(--text-secondary) !important;
}

/* ── Categorías sidebar ── */
.nav-category {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted) !important;
    padding: 0.6rem 0 0.2rem 0;
    border-top: 1px solid var(--border);
    margin-top: 0.4rem;
}
.nav-category:first-child { border-top: none; margin-top: 0; }

/* Categorías destacadas (Cantidades, Componentes, PMTs) */
.nav-category-highlight {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent-blue) !important;
    padding: 0.6rem 0 0.2rem 0;
    border-top: 2px solid var(--border);
    margin-top: 0.6rem;
}

/* ── KPI cards ── */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.5rem;
}
.kpi-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-bottom: 0.25rem;
    font-family: 'IBM Plex Mono', monospace;
}
.kpi-value {
    font-size: 1.55rem;
    font-weight: 600;
    color: var(--kpi-value-color);
    line-height: 1.2;
}
.kpi-sub {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}
.kpi-accent { color: var(--accent-green) !important; }
.kpi-warn   { color: var(--accent-warn)   !important; }
.kpi-danger { color: var(--accent-danger) !important; }
.kpi-info   { color: var(--accent-blue)   !important; }

/* ── Tablas ── */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* ── Botones ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    border-radius: 6px;
}

/* ── Dividers ── */
hr { border-color: var(--border); }

/* ── Expanders ── */
details summary {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}

/* ── Headings ── */
h1, h2, h3 {
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    color: var(--text-primary);
}
h3 {
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.06em;
}
.badge-borrador { background: var(--badge-borrador-bg); color: var(--badge-borrador-fg); }
.badge-revisado { background: var(--badge-revisado-bg); color: var(--badge-revisado-fg); }
.badge-aprobado { background: var(--badge-aprobado-bg); color: var(--badge-aprobado-fg); }
.badge-devuelto { background: var(--badge-devuelto-bg); color: var(--badge-devuelto-fg); }

/* ── Login ── */
.login-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2.5rem 2rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# CONEXIÓN SUPABASE
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def badge(estado: str) -> str:
    cls = {
        'BORRADOR': 'badge-borrador',
        'REVISADO': 'badge-revisado',
        'APROBADO': 'badge-aprobado',
        'DEVUELTO': 'badge-devuelto',
    }.get(estado, 'badge-borrador')
    return f'<span class="badge {cls}">{estado}</span>'


def kpi(label, value, sub="", accent_class=""):
    val_class = f"kpi-value {accent_class}" if accent_class else "kpi-value"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="{val_class}">{value}</div>
        {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# DATA LOADERS
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_cantidades(estados=None, fecha_ini=None, fecha_fin=None):
    """Carga registros_cantidades (formularios de medición de obra)."""
    sb    = get_supabase()
    query = sb.table('registros_cantidades').select('*')
    if estados:
        query = query.in_('estado', estados)
    if fecha_ini:
        query = query.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        query = query.lte('fecha_creacion', fecha_fin)
    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


@st.cache_data(ttl=60)
def load_componentes(estados=None, fecha_ini=None, fecha_fin=None):
    """Carga registros_componentes (formularios ambientales, SST, social)."""
    sb    = get_supabase()
    query = sb.table('registros_componentes').select('*')
    if estados:
        query = query.in_('estado', estados)
    if fecha_ini:
        query = query.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        query = query.lte('fecha_creacion', fecha_fin)
    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


@st.cache_data(ttl=60)
def load_reporte_diario(estados=None, fecha_ini=None, fecha_fin=None):
    """Carga registros_reporte_diario."""
    sb    = get_supabase()
    query = sb.table('registros_reporte_diario').select('*')
    if estados:
        query = query.in_('estado', estados)
    if fecha_ini:
        query = query.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        query = query.lte('fecha_creacion', fecha_fin)
    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_contrato():
    sb = get_supabase()
    r  = sb.table('contratos').select('*').eq('id', 'IDU-1556-2025').execute()
    return r.data[0] if r.data else {}


@st.cache_data(ttl=120)
def load_presupuesto():
    sb = get_supabase()
    r  = sb.table('presupuesto_bd').select('*').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


def clear_cache():
    st.cache_data.clear()


# ══════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def login():
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace; font-size:0.7rem;
                    letter-spacing:0.14em; color:var(--accent-blue); text-transform:uppercase;
                    margin-bottom:0.25rem;">
            Sistema de Bitácora Digital
        </div>
        <div style="font-size:1.8rem; font-weight:600; color:var(--text-primary); margin-bottom:0.1rem;">
            BDO · IDU-1556-2025
        </div>
        <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:2rem;">
            Contrato de obra · Grupo 4 · Mártires, San Cristóbal, Rafael Uribe Uribe, Santafé, Antonio Nariño
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            email    = st.text_input("Correo electrónico", placeholder="usuario@empresa.com")
            password = st.text_input("Contraseña", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            submit   = st.button("Ingresar al sistema", use_container_width=True, type="primary")

        if submit:
            if not email or not password:
                st.error("Ingresa correo y contraseña")
                return
            try:
                sb   = get_supabase()
                resp = sb.auth.sign_in_with_password({"email": email, "password": password})
                if resp.user:
                    perfil = sb.table('perfiles').select('*').eq('id', resp.user.id).execute()
                    if not perfil.data:
                        st.error("Usuario sin perfil configurado. Contacta al administrador.")
                        return
                    st.session_state['user']   = resp.user
                    st.session_state['perfil'] = perfil.data[0]
                    st.rerun()
            except Exception as e:
                st.error(f"Error de autenticación: {e}")


def logout():
    for k in ['user', 'perfil']:
        st.session_state.pop(k, None)
    st.rerun()


# ══════════════════════════════════════════════════════════════
# SIDEBAR Y NAVEGACIÓN
# ══════════════════════════════════════════════════════════════

# Roles activos en el sistema (módulo 005_USUARIOS)
# inspector / obra        → inspectores de campo, crean registros en QField
# residente / coordinador → revisión y aprobación nivel 1
# interventor             → aprobación nivel 2
# supervisor              → solo lectura
# admin                   → acceso total

ROL_LABELS = {
    'inspector':    'Inspector de Campo',
    'obra':         'Personal de Obra',
    'residente':    'Residente de Obra',
    'coordinador':  'Coordinador de Obra',
    'interventor':  'Interventor IDU',
    'supervisor':   'Supervisor IDU',
    'admin':        'Administrador',
}

# Páginas disponibles por rol
NAV_ACCESS = {
    # ── General ──────────────────────────────────────────────
    "Estado Actual":              ['inspector','obra','residente','coordinador',
                                   'interventor','supervisor','admin'],
    "Anotaciones":                ['inspector','obra','residente','coordinador',
                                   'interventor','supervisor','admin'],
    "Generar PDF":                ['residente','coordinador','interventor','supervisor','admin'],
    "Mapa de Obra":               ['residente','coordinador','interventor','supervisor','admin'],
    "Seguimiento Presupuesto":    ['residente','coordinador','interventor','supervisor','admin'],
    # ── Reportes de Cantidades ────────────────────────────────
    "Reporte Cantidades":         ['residente','coordinador','interventor','supervisor','admin'],
    # ── Reportes de Componentes Transversales ─────────────────
    "Componente Ambiental - SST": ['residente','coordinador','interventor','supervisor','admin'],
    "Componente Social":          ['residente','coordinador','interventor','supervisor','admin'],
    # ── Seguimiento de PMTs ───────────────────────────────────
    "Seguimiento PMTs":           ['residente','coordinador','interventor','supervisor','admin'],
}

# Estructura de categorías del menú lateral
# 'highlight': True → categoría destacada con color acento
NAV_CATEGORIES = [
    {
        "label":   "General",
        "highlight": False,
        "pages":   ["Estado Actual", "Anotaciones", "Generar PDF",
                    "Mapa de Obra", "Seguimiento Presupuesto"],
    },
    {
        "label":   "Reportes de Cantidades",
        "highlight": True,
        "pages":   ["Reporte Cantidades"],
    },
    {
        "label":   "Reportes de Componentes Transversales",
        "highlight": True,
        "pages":   ["Componente Ambiental - SST", "Componente Social"],
    },
    {
        "label":   "Seguimiento de PMTs",
        "highlight": True,
        "pages":   ["Seguimiento PMTs"],
    },
]


def sidebar(perfil):
    rol = perfil['rol']

    with st.sidebar:
        # Header usuario
        st.markdown(f"""
        <div style="padding:1rem 0 0.5rem 0; border-bottom:1px solid var(--border); margin-bottom:0.5rem;">
            <div style="font-size:0.72rem; color:var(--text-muted); font-family:'IBM Plex Mono',monospace;
                        text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.2rem;">
                {ROL_LABELS.get(rol, rol)}
            </div>
            <div style="font-size:1rem; font-weight:600; color:var(--text-primary);">{perfil['nombre']}</div>
            <div style="font-size:0.78rem; color:var(--text-secondary);">{perfil.get('empresa','')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Resumen rápido (cantidades)
        df_q = load_cantidades()
        if not df_q.empty:
            total = len(df_q)
            apr   = len(df_q[df_q['estado'] == 'APROBADO'])
            dev   = len(df_q[df_q['estado'] == 'DEVUELTO'])
            st.markdown(f"""
            <div style="display:flex; gap:0.5rem; margin-bottom:0.75rem; flex-wrap:wrap;">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
                             background:var(--bg-card);border:1px solid var(--border);border-radius:4px;
                             padding:2px 7px;color:var(--text-muted);">Total {total}</span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
                             background:var(--badge-aprobado-bg);border-radius:4px;padding:2px 7px;
                             color:var(--badge-aprobado-fg);">Aprobados {apr}</span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
                             background:var(--badge-devuelto-bg);border-radius:4px;padding:2px 7px;
                             color:var(--badge-devuelto-fg);">Devueltos {dev}</span>
            </div>
            """, unsafe_allow_html=True)

        # Navegación por categorías
        opciones_disponibles = []
        for cat in NAV_CATEGORIES:
            accesibles = [p for p in cat["pages"] if rol in NAV_ACCESS.get(p, [])]
            for p in accesibles:
                if p not in opciones_disponibles:
                    opciones_disponibles.append(p)

        selected_page = st.session_state.get(
            'current_page',
            opciones_disponibles[0] if opciones_disponibles else "Estado Actual"
        )

        for cat in NAV_CATEGORIES:
            accesibles = [p for p in cat["pages"] if rol in NAV_ACCESS.get(p, [])]
            if not accesibles:
                continue

            cat_class = "nav-category-highlight" if cat["highlight"] else "nav-category"
            st.markdown(f'<div class="{cat_class}">{cat["label"]}</div>', unsafe_allow_html=True)

            for page in accesibles:
                is_active = selected_page == page
                if st.button(
                    page,
                    key=f"nav_{page}",
                    use_container_width=True,
                ):
                    st.session_state['current_page'] = page
                    st.rerun()

        st.divider()
        if st.button("Cerrar sesión", use_container_width=True):
            logout()

    return st.session_state.get(
        'current_page',
        opciones_disponibles[0] if opciones_disponibles else "Estado Actual"
    )


# ══════════════════════════════════════════════════════════════
# BITÁCORA 1 — ESTADO ACTUAL
# ══════════════════════════════════════════════════════════════

def page_estado_actual():
    st.markdown("### Estado Actual del Contrato")

    contrato = load_contrato()

    if not contrato:
        st.info("Sin datos de contrato configurados. Verifica la tabla 'contratos' en Supabase.")
        contrato = {
            "numero": "IDU-1556-2025",
            "objeto": "Mantenimiento y rehabilitación de vías locales — Grupo 4",
            "entidad": "Instituto de Desarrollo Urbano (IDU)",
            "contratista": "SERVIALCO S.A.S.",
            "valor_inicial": 8_500_000_000,
            "valor_actualizado": 8_500_000_000,
            "plazo_dias": 180,
            "fecha_inicio": "2025-02-01",
            "anticipos_total": 1,
            "valor_anticipo": 2_550_000_000,
            "valor_amortizado": 850_000_000,
            "adicion_plazo_dias": 0,
            "adicion_valor": 0,
            "valor_ejecutado": 3_200_000_000,
        }

    fecha_inicio = datetime.strptime(contrato.get('fecha_inicio', '2025-01-01'), '%Y-%m-%d').date()
    plazo        = int(contrato.get('plazo_dias', 0)) + int(contrato.get('adicion_plazo_dias', 0) or 0)
    dias_trans   = (date.today() - fecha_inicio).days
    dias_rest    = max(plazo - dias_trans, 0)
    pct_tiempo   = round(min(dias_trans / plazo * 100, 100)) if plazo > 0 else 0

    val_ini      = safe_float(contrato.get('valor_inicial')) or 0
    val_act      = safe_float(contrato.get('valor_actualizado')) or val_ini
    val_ejec     = safe_float(contrato.get('valor_ejecutado')) or 0
    pct_ejec     = round(val_ejec / val_act * 100, 1) if val_act > 0 else 0

    val_ant      = safe_float(contrato.get('valor_anticipo')) or 0
    val_amort    = safe_float(contrato.get('valor_amortizado')) or 0
    pct_amort    = round(val_amort / val_ant * 100, 1) if val_ant > 0 else 0

    st.markdown("#### Información General")
    c1, c2, c3 = st.columns(3)

    with c1:
        kpi("Número de Contrato", contrato.get('numero', '—'))
        kpi("Entidad Contratante", contrato.get('entidad', '—'))

    with c2:
        kpi("Contratista", contrato.get('contratista', '—'))
        kpi("Fecha de Inicio", fecha_inicio.strftime('%d/%m/%Y'))

    with c3:
        kpi("Plazo Total", f"{plazo} días",
            sub=f"+{contrato.get('adicion_plazo_dias', 0) or 0} días de adición")
        kpi("Grupos / Localidades",
            "Mártires · S.Cristóbal · R.Uribe<br>Santafé · A.Nariño",
            accent_class="kpi-info")

    st.markdown(f"""
    <div class="kpi-card" style="margin-bottom:1rem;">
        <div class="kpi-label">Objeto del Contrato</div>
        <div style="color:var(--text-secondary); font-size:0.95rem; line-height:1.5;">
            {contrato.get('objeto', '—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("#### Ejecución del Plazo")
    ct1, ct2, ct3, ct4 = st.columns(4)

    accent_tiempo = "kpi-warn" if pct_tiempo > 70 else "kpi-accent"
    with ct1: kpi("Días Transcurridos", str(dias_trans), sub=f"{pct_tiempo}% del plazo", accent_class=accent_tiempo)
    with ct2: kpi("Días Restantes", str(dias_rest))
    with ct3: kpi("Plazo Original", f"{contrato.get('plazo_dias', '—')} días")
    with ct4: kpi("Adiciones de Plazo", f"{contrato.get('adicion_plazo_dias', 0) or 0} días",
                  accent_class="kpi-warn" if (contrato.get('adicion_plazo_dias') or 0) > 0 else "")

    fig_tiempo = go.Figure(go.Bar(
        x=[pct_tiempo, 100 - pct_tiempo],
        y=["Plazo"],
        orientation='h',
        marker_color=['#388bfd', '#e2e8f0'],
        text=[f"{pct_tiempo}% transcurrido", f"{100 - pct_tiempo}% restante"],
        textposition='inside',
        textfont=dict(family="IBM Plex Mono", size=12, color="white"),
    ))
    fig_tiempo.update_layout(
        height=70, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, barmode='stack',
        xaxis=dict(showticklabels=False, range=[0, 100]),
        yaxis=dict(showticklabels=False),
    )
    st.plotly_chart(fig_tiempo, use_container_width=True, config={'displayModeBar': False})

    st.divider()

    st.markdown("#### Ejecución Financiera")
    cf1, cf2, cf3, cf4 = st.columns(4)

    pct_ejec_accent = "kpi-danger" if pct_ejec < pct_tiempo - 15 else (
        "kpi-accent" if pct_ejec >= 80 else "kpi-warn"
    )
    with cf1: kpi("Valor Contrato", f"${val_act:,.0f}", sub="Actualizado con adiciones", accent_class="kpi-info")
    with cf2: kpi("Valor Ejecutado", f"${val_ejec:,.0f}", sub=f"{pct_ejec}% del contrato", accent_class=pct_ejec_accent)
    with cf3: kpi("Anticipos Desembolsados", f"${val_ant:,.0f}",
                  sub=f"{contrato.get('anticipos_total', 0)} anticipo(s)")
    with cf4: kpi("Amortizado", f"${val_amort:,.0f}", sub=f"{pct_amort}% del anticipo",
                  accent_class="kpi-accent" if pct_amort > 50 else "kpi-warn")

    if contrato.get('adicion_valor') and contrato['adicion_valor'] > 0:
        st.markdown(f"""
        <div class="kpi-card" style="border-color:var(--accent-warn); margin-top:0.5rem;">
            <div class="kpi-label kpi-warn">Adición de Valor</div>
            <div class="kpi-value kpi-warn">${contrato['adicion_valor']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_fin = go.Figure()
        fig_fin.add_trace(go.Bar(
            name='Ejecutado', x=['Financiero'], y=[pct_ejec],
            marker_color='#3fb950', text=[f"{pct_ejec}%"], textposition='inside',
            textfont=dict(family="IBM Plex Mono", size=13, color="white"),
        ))
        fig_fin.add_trace(go.Bar(
            name='Pendiente', x=['Financiero'], y=[100 - pct_ejec],
            marker_color='#e2e8f0',
        ))
        fig_fin.add_trace(go.Bar(
            name='Tiempo', x=['Tiempo'], y=[pct_tiempo],
            marker_color='#388bfd', text=[f"{pct_tiempo}%"], textposition='inside',
            textfont=dict(family="IBM Plex Mono", size=13, color="white"),
        ))
        fig_fin.add_trace(go.Bar(
            name='Tiempo rest.', x=['Tiempo'], y=[100 - pct_tiempo],
            marker_color='#e2e8f0',
        ))
        fig_fin.update_layout(
            barmode='stack', height=220,
            margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            yaxis=dict(range=[0, 100], ticksuffix='%'),
            font=dict(family='IBM Plex Sans'),
            title=dict(text='Ejecución Financiera vs Tiempo (%)', font=dict(size=12)),
        )
        st.plotly_chart(fig_fin, use_container_width=True, config={'displayModeBar': False})

    with col_g2:
        fig_ant = go.Figure(go.Pie(
            values=[val_amort, val_ant - val_amort],
            labels=['Amortizado', 'Pendiente'],
            hole=0.65,
            marker_colors=['#388bfd', '#e2e8f0'],
            textinfo='none',
        ))
        fig_ant.add_annotation(
            text=f"{pct_amort}%<br><span style='font-size:10px'>amortizado</span>",
            x=0.5, y=0.5, font_size=18,
            showarrow=False, font=dict(family='IBM Plex Mono'),
        )
        fig_ant.update_layout(
            height=220, margin=dict(l=0, r=0, t=20, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            title=dict(text='Amortización de Anticipos', font=dict(size=12)),
        )
        st.plotly_chart(fig_ant, use_container_width=True, config={'displayModeBar': False})


# ══════════════════════════════════════════════════════════════
# BITÁCORA 2 — ANOTACIONES (registros_cantidades)
# ══════════════════════════════════════════════════════════════

# Configuración de flujo de aprobación por rol
# Formato: rol → (estados visibles, estado al aprobar, dict de campos)
APROBACION_CONFIG = {
    'inspector':    (None,                    None,       None),
    'obra':         (None,                    None,       None),
    'residente':    (['BORRADOR', 'DEVUELTO'], 'REVISADO', {
        'campo_cant':   'cant_residente',
        'campo_estado': 'estado_residente',
        'campo_apr':    'aprobado_residente',
        'campo_fecha':  'fecha_residente',
        'campo_obs':    'obs_residente',
    }),
    'coordinador':  (['BORRADOR', 'DEVUELTO'], 'REVISADO', {
        'campo_cant':   'cant_residente',
        'campo_estado': 'estado_residente',
        'campo_apr':    'aprobado_residente',
        'campo_fecha':  'fecha_residente',
        'campo_obs':    'obs_residente',
    }),
    'interventor':  (['REVISADO'],             'APROBADO', {
        'campo_cant':   'cant_interventor',
        'campo_estado': 'estado_interventor',
        'campo_apr':    'aprobado_interventor',
        'campo_fecha':  'fecha_interventor',
        'campo_obs':    'obs_interventor',
    }),
    'supervisor':   (None,                    None,       None),
    'admin':        (['REVISADO'],             'APROBADO', {
        'campo_cant':   'cant_interventor',
        'campo_estado': 'estado_interventor',
        'campo_apr':    'aprobado_interventor',
        'campo_fecha':  'fecha_interventor',
        'campo_obs':    'obs_interventor',
    }),
}


def page_anotaciones(perfil):
    rol = perfil['rol']
    st.markdown("### Anotaciones de Bitácora")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    c1, c2, c3, c4 = st.columns(4)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=15))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3:
        if estados_vis:
            estado_f = st.selectbox("Estado", ["Todos"] + estados_vis)
        else:
            estado_f = st.selectbox("Estado", ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"])
    with c4:
        buscar = st.text_input("Folio / Actividad / CIV")

    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis

    df = load_cantidades(estados=estados_q,
                         fecha_ini=fi.isoformat(),
                         fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = (
            df.get('folio', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False) |
            df.get('tipo_actividad', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False) |
            df.get('civ', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("No hay registros para los filtros seleccionados")
        return

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total", len(df))
    with m2: st.metric("Borradores", len(df[df['estado'] == 'BORRADOR']) if 'estado' in df else 0)
    with m3: st.metric("Revisados",  len(df[df['estado'] == 'REVISADO'])  if 'estado' in df else 0)
    with m4: st.metric("Aprobados",  len(df[df['estado'] == 'APROBADO'])  if 'estado' in df else 0)

    st.divider()

    # Vista solo lectura (inspector / obra / supervisor)
    if not campos:
        cols = ['folio', 'usuario_qfield', 'id_tramo', 'civ', 'tipo_actividad',
                'cantidad', 'unidad', 'estado', 'fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    st.markdown(f"**{len(df)} registro(s) pendiente(s) de revisión**")

    for _, reg in df.iterrows():
        estado_actual = reg.get('estado', '')
        folio         = reg.get('folio', '—')
        actividad     = reg.get('tipo_actividad', '—')
        tramo         = reg.get('tramo_descripcion', reg.get('id_tramo', '—'))

        with st.expander(f"**{folio}** · {actividad} · {tramo}", expanded=False):
            ci, ca = st.columns([2.2, 1])

            with ci:
                st.markdown(f"""
                <div style="display:flex; gap:0.5rem; margin-bottom:0.75rem; flex-wrap:wrap;">
                    {badge(estado_actual)}
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;
                                 color:var(--text-muted);">
                        {str(reg.get('fecha_inicio', ''))[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield', '—')}")
                    st.markdown(f"**Tramo:** {reg.get('id_tramo', '—')}")
                    st.markdown(f"**CIV:** {reg.get('civ', '—')}")
                with col_b:
                    st.markdown(f"**Item pago:** {reg.get('item_pago', '—')}")
                    st.markdown(f"**Cod. elemento:** {reg.get('codigo_elemento', '—')}")
                    st.markdown(f"**Unidad:** {reg.get('unidad', '—')}")
                with col_c:
                    cant = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cant. inspector", f"{cant:.2f} {reg.get('unidad', '')}")
                    if reg.get('cant_residente'):
                        st.metric("Cant. residente",
                                  f"{safe_float(reg.get('cant_residente') or 0):.2f}")

                if reg.get('descripcion'):
                    st.info(reg['descripcion'])

                if reg.get('obs_residente') and rol in ('interventor', 'admin'):
                    st.warning(f"Obs. residente: {reg['obs_residente']}")

                # Adjunto de campo
                if reg.get('documento_adj'):
                    st.caption(f"Adjunto: {reg['documento_adj']}")

            # Panel de aprobación
            with ca:
                st.markdown("**Validación**")
                campo_cant = campos['campo_cant']
                campo_obs  = campos['campo_obs']

                cant_def = (safe_float(reg.get(campo_cant)) or
                            safe_float(reg.get('cantidad')) or 0.0)

                cant_val = st.number_input(
                    "Cantidad validada", value=float(cant_def),
                    step=0.01, key=f"cant_{reg['id']}"
                )
                obs_val = st.text_area(
                    "Observación", key=f"obs_{reg['id']}",
                    height=80,
                    placeholder="Opcional para aprobar · Obligatoria para devolver"
                )

                b1, b2 = st.columns(2)

                with b1:
                    if st.button("Aprobar", key=f"apr_{reg['id']}",
                                 use_container_width=True, type="primary"):
                        try:
                            sb = get_supabase()
                            update_data = {
                                'estado':               estado_apr,
                                campo_cant:             cant_val,
                                campos['campo_estado']: 'aprobado',
                                campos['campo_apr']:    perfil['id'],
                                campos['campo_fecha']:  datetime.now().isoformat(),
                            }
                            if obs_val:
                                update_data[campo_obs] = obs_val
                            sb.table('registros_cantidades').update(update_data)\
                              .eq('id', reg['id']).execute()
                            clear_cache()
                            st.success("Registro aprobado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al aprobar: {e}")

                with b2:
                    if st.button("Devolver", key=f"dev_{reg['id']}",
                                 use_container_width=True):
                        if not obs_val:
                            st.error("Escribe una observación para devolver")
                        else:
                            try:
                                sb = get_supabase()
                                sb.table('registros_cantidades').update({
                                    'estado':               'DEVUELTO',
                                    campos['campo_estado']: 'devuelto',
                                    campo_obs:              obs_val,
                                    campos['campo_fecha']:  datetime.now().isoformat(),
                                }).eq('id', reg['id']).execute()
                                clear_cache()
                                st.warning("Registro devuelto al inspector")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al devolver: {e}")


# ══════════════════════════════════════════════════════════════
# BITÁCORA 3 — GENERAR PDF
# ══════════════════════════════════════════════════════════════

def page_generar_pdf(perfil):
    st.markdown("### Generar PDF de Bitácora")
    st.info("Módulo en desarrollo. La generación de PDF se implementará con Jinja2 + WeasyPrint.")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    tipo_reporte = st.selectbox(
        "Tipo de reporte",
        ["Bitácora semanal completa", "Solo actividades aprobadas", "Solo anotaciones"]
    )

    incluir = st.multiselect(
        "Incluir secciones",
        ["Registro de actividades", "Anotaciones", "Cantidades por item"],
        default=["Registro de actividades", "Anotaciones"]
    )

    df = load_cantidades(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if not df.empty:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Vista previa del reporte</div>
            <div style="color:var(--text-secondary); margin-top:0.5rem;">
                Período: {fi.strftime('%d/%m/%Y')} — {ff.strftime('%d/%m/%Y')}<br>
                Registros incluidos: <strong>{len(df)}</strong><br>
                Aprobados: <strong>{len(df[df['estado'] == 'APROBADO'])}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.button("Generar y descargar PDF", type="primary",
              disabled=True, use_container_width=False)
    st.caption("Próximamente disponible — módulo de PDF en construcción")


# ══════════════════════════════════════════════════════════════
# MAPA DE OBRA
# ══════════════════════════════════════════════════════════════

def page_mapa(perfil):
    st.markdown("### Mapa de Obra")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=30))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df = load_cantidades(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if df.empty or 'latitud' not in df.columns or 'longitud' not in df.columns:
        st.info("No hay registros con coordenadas para el período seleccionado.")
        return

    df_geo = df.dropna(subset=['latitud', 'longitud']).copy()
    df_geo['latitud']  = pd.to_numeric(df_geo['latitud'],  errors='coerce')
    df_geo['longitud'] = pd.to_numeric(df_geo['longitud'], errors='coerce')
    df_geo = df_geo.dropna(subset=['latitud', 'longitud'])

    if df_geo.empty:
        st.info("No hay registros con coordenadas válidas.")
        return

    color_map = {
        'BORRADOR': '#8b949e',
        'REVISADO': '#3fb950',
        'APROBADO': '#388bfd',
        'DEVUELTO': '#f85149',
    }

    fig = px.scatter_mapbox(
        df_geo,
        lat='latitud',
        lon='longitud',
        color='estado' if 'estado' in df_geo else None,
        color_discrete_map=color_map,
        hover_data=['folio', 'tipo_actividad', 'id_tramo', 'cantidad', 'unidad']
                   if all(c in df_geo.columns for c in ['folio', 'tipo_actividad']) else None,
        zoom=12,
        height=560,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", y=0.01, x=0.01),
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# SEGUIMIENTO PRESUPUESTO
# ══════════════════════════════════════════════════════════════

def page_presupuesto(perfil):
    st.markdown("### Seguimiento Presupuestal")

    df = load_presupuesto()

    if df.empty:
        st.info("No hay datos de presupuesto disponibles. Verifica la tabla 'presupuesto_bd'.")
        return

    # Columnas posibles según el esquema presupuesto_bd
    cols_show = [c for c in [
        'componente', 'compenente',   # acepta typo del GPKG
        'item_pago', 'descripcion', 'und',
        'cantidad_contrato', 'valor_unitario', 'valor_total',
        'cantidad_ejecutada', 'valor_ejecutado', 'pct_ejecutado',
    ] if c in df.columns]

    # Normalizar nombre del campo componente (puede venir con typo)
    if 'compenente' in df.columns and 'componente' not in df.columns:
        df = df.rename(columns={'compenente': 'componente'})
        if 'componente' not in cols_show:
            cols_show = ['componente'] + [c for c in cols_show if c != 'compenente']

    if not cols_show:
        st.dataframe(df, hide_index=True, use_container_width=True)
        return

    # KPIs financieros
    if 'valor_total' in df.columns:
        total_contrato = df['valor_total'].apply(safe_float).sum()
        m1, m2 = st.columns(2)
        with m1:
            kpi("Valor Total Contrato", f"${total_contrato:,.0f}", accent_class="kpi-info")
        if 'valor_ejecutado' in df.columns:
            total_ejec = df['valor_ejecutado'].apply(safe_float).sum()
            pct_e = round(total_ejec / total_contrato * 100, 1) if total_contrato > 0 else 0
            with m2:
                kpi("Valor Ejecutado", f"${total_ejec:,.0f}",
                    sub=f"{pct_e}% del contrato",
                    accent_class="kpi-accent" if pct_e >= 70 else "kpi-warn")
        st.divider()

    # Agrupación por componente
    if 'componente' in df.columns and 'valor_total' in df.columns:
        df_grp = df.groupby('componente').agg(
            valor_total=('valor_total', lambda x: x.apply(safe_float).sum())
        ).reset_index()
        if not df_grp.empty:
            fig = px.bar(df_grp, x='componente', y='valor_total',
                         title='Valor Presupuestado por Componente',
                         height=300)
            fig.update_layout(
                margin=dict(l=0, r=0, t=30, b=0),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='IBM Plex Sans'),
                xaxis_title='', yaxis_title='Valor ($)',
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.dataframe(
        df[cols_show],
        hide_index=True,
        use_container_width=True,
        column_config={
            'valor_total':      st.column_config.NumberColumn('Valor Total ($)',      format="$%.0f"),
            'valor_ejecutado':  st.column_config.NumberColumn('Valor Ejecutado ($)',  format="$%.0f"),
            'valor_unitario':   st.column_config.NumberColumn('Valor Unitario ($)',   format="$%.0f"),
            'pct_ejecutado':    st.column_config.ProgressColumn('Ejecutado (%)', format="%.1f%%",
                                                                  min_value=0, max_value=100),
        }
    )

    csv = df[cols_show].to_csv(index=False).encode('utf-8')
    st.download_button(
        "Exportar CSV",
        data=csv,
        file_name="Presupuesto_IDU-1556-2025.csv",
        mime="text/csv"
    )


# ══════════════════════════════════════════════════════════════
# REPORTES DE CANTIDADES
# ══════════════════════════════════════════════════════════════

def page_reporte_cantidades(perfil):
    rol = perfil['rol']
    st.markdown("### Reportes de Cantidades")

    c1, c2, c3 = st.columns(3)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=15))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3: buscar = st.text_input("Folio / Actividad")

    df = load_cantidades(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = (
            df.get('folio', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False) |
            df.get('tipo_actividad', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("No hay registros para el período seleccionado")
        return

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total registros", len(df))
    with m2: st.metric("Aprobados", len(df[df['estado'] == 'APROBADO']) if 'estado' in df else 0)
    with m3: st.metric("Pendientes",
                        len(df[df['estado'].isin(['BORRADOR', 'DEVUELTO'])]) if 'estado' in df else 0)
    with m4:
        if 'cantidad' in df.columns:
            total_cant = df['cantidad'].apply(safe_float).sum()
            st.metric("Suma cantidades", f"{total_cant:,.2f}")

    st.divider()

    cols_show = ['folio', 'usuario_qfield', 'id_tramo', 'civ', 'codigo_elemento',
                 'tipo_actividad', 'item_pago', 'item_descripcion',
                 'cantidad', 'unidad', 'cant_residente', 'cant_interventor', 'estado']
    cols_show = [c for c in cols_show if c in df.columns]

    st.dataframe(
        df[cols_show],
        hide_index=True,
        use_container_width=True,
        column_config={
            'cantidad':         st.column_config.NumberColumn('Cant. Inspector',   format="%.2f"),
            'cant_residente':   st.column_config.NumberColumn('Cant. Residente',   format="%.2f"),
            'cant_interventor': st.column_config.NumberColumn('Cant. Interventor', format="%.2f"),
            'estado':           st.column_config.TextColumn('Estado'),
        }
    )

    # Adjuntos de campo (documento_adj)
    st.divider()
    st.markdown("#### Registros con adjunto de campo")

    if 'documento_adj' in df.columns:
        df_adj = df[df['documento_adj'].notna() & (df['documento_adj'] != '')]
        if df_adj.empty:
            st.caption("No hay registros con adjunto en el período seleccionado.")
        else:
            for _, reg in df_adj.head(10).iterrows():
                with st.expander(
                    f"**{reg.get('folio', '—')}** · {reg.get('tipo_actividad', '—')}",
                    expanded=False
                ):
                    st.markdown(f"CIV: `{reg.get('civ', '—')}` · Item: `{reg.get('item_pago', '—')}` "
                                f"· Cod. elemento: `{reg.get('codigo_elemento', '—')}`")
                    st.caption(f"Adjunto: {reg['documento_adj']}")
    else:
        st.caption("No hay columna de adjuntos disponible.")

    # Exportar CSV
    csv = df[cols_show].to_csv(index=False).encode('utf-8')
    st.download_button(
        "Exportar CSV",
        data=csv,
        file_name=f"Cantidades_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


# ══════════════════════════════════════════════════════════════
# REPORTES DE COMPONENTES TRANSVERSALES — base común
# ══════════════════════════════════════════════════════════════

def panel_componentes_base(perfil, filtro_tipo=None):
    """
    Panel base para Ambiental/SST y Social.
    Carga de registros_componentes con opción de filtrar por tipo.
    """
    rol = perfil['rol']

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df = load_componentes(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    # Filtrar por tipo de componente si se especifica
    if filtro_tipo and not df.empty and 'tipo_componente' in df.columns:
        df = df[df['tipo_componente'].str.contains(filtro_tipo, case=False, na=False)]

    # KPIs
    st.markdown("#### Resumen del período")
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1: kpi("Total registros", str(len(df)))
    with kc2: kpi("Aprobados",
                   str(len(df[df['estado'] == 'APROBADO'])) if not df.empty and 'estado' in df else "0",
                   accent_class="kpi-accent")
    with kc3: kpi("Pendientes",
                   str(len(df[df['estado'].isin(['BORRADOR', 'DEVUELTO'])])) if not df.empty and 'estado' in df else "0")
    with kc4: kpi("Devueltos",
                   str(len(df[df['estado'] == 'DEVUELTO'])) if not df.empty and 'estado' in df else "0",
                   accent_class="kpi-danger" if not df.empty and 'estado' in df and len(df[df['estado'] == 'DEVUELTO']) > 0 else "")

    st.divider()
    st.markdown("#### Registros del período")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    if df.empty:
        st.info("Sin registros para el período seleccionado")
        return

    if not campos:
        # Solo lectura
        cols = ['folio', 'usuario_qfield', 'id_tramo', 'tipo_componente',
                'estado', 'fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    df_vis = df[df['estado'].isin(estados_vis)] if estados_vis else df

    if df_vis.empty:
        st.success("No hay registros pendientes")
    else:
        st.markdown(f"**{len(df_vis)} pendiente(s)**")

        for _, reg in df_vis.iterrows():
            with st.expander(
                f"**{reg.get('folio', '—')}** · {reg.get('tipo_componente', reg.get('tipo_actividad', '—'))}",
                expanded=False
            ):
                ci, ca = st.columns([2, 1])
                with ci:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield', '—')} &nbsp;|&nbsp; "
                                f"**Tramo:** {reg.get('id_tramo', '—')}")
                    cant = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cantidad reportada", f"{cant:.2f} {reg.get('unidad', '')}")
                    if reg.get('descripcion'):
                        st.info(reg['descripcion'])

                with ca:
                    campo_cant = campos['campo_cant']
                    campo_obs  = campos['campo_obs']
                    cant_def   = (safe_float(reg.get(campo_cant)) or
                                  safe_float(reg.get('cantidad')) or 0.0)

                    cant_val = st.number_input("Cant. validada", value=float(cant_def),
                                               step=0.01, key=f"tx_cant_{reg['id']}")
                    obs_val  = st.text_area("Observación", key=f"tx_obs_{reg['id']}",
                                            height=70,
                                            placeholder="Opcional / Obligatoria para devolver")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("Aprobar", key=f"tx_apr_{reg['id']}",
                                     use_container_width=True, type="primary"):
                            try:
                                sb = get_supabase()
                                upd = {
                                    'estado':               estado_apr,
                                    campo_cant:             cant_val,
                                    campos['campo_estado']: 'aprobado',
                                    campos['campo_apr']:    perfil['id'],
                                    campos['campo_fecha']:  datetime.now().isoformat(),
                                }
                                if obs_val:
                                    upd[campo_obs] = obs_val
                                sb.table('registros_componentes').update(upd)\
                                  .eq('id', reg['id']).execute()
                                clear_cache()
                                st.rerun()
                            except Exception as e:
                                st.error(str(e))
                    with b2:
                        if st.button("Devolver", key=f"tx_dev_{reg['id']}",
                                     use_container_width=True):
                            if not obs_val:
                                st.error("Escribe observación")
                            else:
                                try:
                                    sb = get_supabase()
                                    sb.table('registros_componentes').update({
                                        'estado':               'DEVUELTO',
                                        campos['campo_estado']: 'devuelto',
                                        campo_obs:              obs_val,
                                        campos['campo_fecha']:  datetime.now().isoformat(),
                                    }).eq('id', reg['id']).execute()
                                    clear_cache()
                                    st.rerun()
                                except Exception as e:
                                    st.error(str(e))


def page_ambiental(perfil):
    st.markdown("### Componente Ambiental y SST")
    panel_componentes_base(perfil, filtro_tipo='ambiental')


def page_social(perfil):
    st.markdown("### Componente Social")
    panel_componentes_base(perfil, filtro_tipo='social')


# ══════════════════════════════════════════════════════════════
# SEGUIMIENTO DE PMTs
# ══════════════════════════════════════════════════════════════

def page_pmt(perfil):
    st.markdown("### Seguimiento de PMTs")

    # Tabla PMTs activos
    try:
        sb     = get_supabase()
        r      = sb.table('pmts').select('*').execute()
        df_pmt = pd.DataFrame(r.data) if r.data else pd.DataFrame()
    except Exception:
        df_pmt = pd.DataFrame()

    if df_pmt.empty:
        st.info("Sin registros de PMTs. Configura la tabla 'pmts' en Supabase.")
        df_pmt = pd.DataFrame({
            'codigo':       ['PMT-01', 'PMT-02', 'PMT-03'],
            'tramo':        ['Av. Boyacá x Calle 3', 'Carrera 10 x Calle 1S', 'Av. Caracas x Calle 14S'],
            'estado':       ['ACTIVO', 'VENCIDO', 'ACTIVO'],
            'vigencia':     ['2025-05-01', '2025-03-15', '2025-06-30'],
            'observaciones':['OK', 'Renovar', 'Modificar por desvío'],
        })

    # KPIs
    k1, k2, k3 = st.columns(3)
    activos  = len(df_pmt[df_pmt['estado'] == 'ACTIVO'])  if 'estado' in df_pmt else 0
    vencidos = len(df_pmt[df_pmt['estado'] == 'VENCIDO']) if 'estado' in df_pmt else 0
    total    = len(df_pmt)
    with k1: kpi("PMTs Totales", str(total))
    with k2: kpi("PMTs Activos",  str(activos),  accent_class="kpi-accent")
    with k3: kpi("PMTs Vencidos", str(vencidos),
                  accent_class="kpi-danger" if vencidos > 0 else "")

    st.divider()
    st.markdown("#### Listado de PMTs")
    st.dataframe(df_pmt, hide_index=True, use_container_width=True)

    # Panel de registros de componentes asociados al PMT
    st.divider()
    st.markdown("#### Registros de Campo Asociados")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df_comp = load_componentes(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if df_comp.empty:
        st.info("No hay registros de componentes en el período.")
    else:
        cols = ['folio', 'usuario_qfield', 'id_tramo', 'tipo_componente', 'estado', 'fecha_creacion']
        cols = [c for c in cols if c in df_comp.columns]
        st.dataframe(df_comp[cols], hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# MAPA DE PÁGINAS Y MAIN
# ══════════════════════════════════════════════════════════════

PAGE_MAP = {
    "Estado Actual":              page_estado_actual,
    "Anotaciones":                page_anotaciones,
    "Generar PDF":                page_generar_pdf,
    "Mapa de Obra":               page_mapa,
    "Seguimiento Presupuesto":    page_presupuesto,
    "Reporte Cantidades":         page_reporte_cantidades,
    "Componente Ambiental - SST": page_ambiental,
    "Componente Social":          page_social,
    "Seguimiento PMTs":           page_pmt,
}


def main():
    if 'user' not in st.session_state:
        login()
        return

    perfil = st.session_state['perfil']
    page   = sidebar(perfil)

    fn = PAGE_MAP.get(page)
    if fn:
        try:
            import inspect
            sig = inspect.signature(fn)
            if sig.parameters:
                fn(perfil)
            else:
                fn()
        except Exception as e:
            st.error(f"Error al cargar la página: {e}")
    else:
        st.error(f"Página '{page}' no encontrada")


if __name__ == '__main__':
    main()
