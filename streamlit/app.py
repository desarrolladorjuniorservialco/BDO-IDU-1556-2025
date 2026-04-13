"""
app.py  ·  BDO IDU-1556-2025
Bitácora Digital de Obra — Contrato IDU-1556-2025 Grupo 4
"""

import os, math, io
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
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════
# ESTILOS — paleta IDU Bogotá, dark/light aware
# ══════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ── CSS variables ── */
:root {
    --idu-red:      #C8102E;
    --idu-red-dim:  #8B0A1F;
    --idu-red-lt:   #F0324E;
    --color-bg:     #0d1117;
    --color-surf:   #161b22;
    --color-surf2:  #1c2333;
    --color-bord:   #21262d;
    --color-text:   #e6edf3;
    --color-mute:   #8b949e;
    --color-dim:    #6e7681;
    --success:      #3fb950;
    --warning:      #d29922;
    --danger:       #f85149;
    --info:         #388bfd;
}

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Dark base ── */
.stApp { background: var(--color-bg); color: var(--color-text); }

/* ── Sidebar dark ── */
section[data-testid="stSidebar"] {
    background: #090d14 !important;
    border-right: 1px solid var(--color-bord);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label {
    color: var(--color-mute) !important;
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Nav categories ── */
.nav-category {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--idu-red) !important;
    padding: 0.65rem 0 0.25rem 0;
    border-top: 1px solid var(--color-bord);
    margin-top: 0.5rem;
}
.nav-category:first-child { border-top: none; margin-top: 0; }

/* ── KPI cards ── */
.kpi-card {
    background: var(--color-surf);
    border: 1px solid var(--color-bord);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.15s ease;
}
.kpi-card:hover { border-color: #444d56; }
.kpi-card-red   { border-left: 3px solid var(--idu-red); }
.kpi-card-green { border-left: 3px solid var(--success); }
.kpi-card-blue  { border-left: 3px solid var(--info); }
.kpi-card-warn  { border-left: 3px solid var(--warning); }

.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--color-mute);
    margin-bottom: 0.2rem;
}
.kpi-value {
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--color-text);
    line-height: 1.2;
}
.kpi-sub {
    font-size: 0.74rem;
    color: var(--color-dim);
    margin-top: 0.12rem;
}
.kpi-idu    { color: var(--idu-red) !important; }
.kpi-accent { color: var(--success); }
.kpi-warn   { color: var(--warning); }
.kpi-danger { color: var(--danger); }
.kpi-info   { color: var(--info); }

/* ── Section title ── */
.sec-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--idu-red);
    padding-bottom: 0.35rem;
    border-bottom: 1px solid var(--color-bord);
    margin-bottom: 0.9rem;
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-borrador { background: #21262d; color: #8b949e; }
.badge-revisado { background: #1f3d2b; color: #3fb950; }
.badge-aprobado { background: #1a3255; color: #79c0ff; }
.badge-devuelto { background: #3d1e1e; color: #f85149; }

/* ── Tipo tags ── */
.tipo-tag {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 4px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.tipo-general    { background: rgba(56,139,253,0.15); color: #79c0ff; }
.tipo-clima      { background: rgba(63,185,80,0.12);  color: #56d364; }
.tipo-maquinaria { background: rgba(210,153,34,0.15); color: #e3b341; }
.tipo-personal   { background: rgba(121,192,255,0.1); color: #79c0ff; }
.tipo-sst        { background: rgba(248,81,73,0.12);  color: #ffa198; }
.tipo-social     { background: rgba(200,16,46,0.12);  color: #ff8fa3; }
.tipo-ambiental  { background: rgba(63,185,80,0.15);  color: #3fb950; }
.tipo-pmt        { background: rgba(210,153,34,0.15); color: #d29922; }
.tipo-cant       { background: rgba(56,139,253,0.12); color: #388bfd; }

/* ── Approval panel ── */
.apr-panel {
    background: var(--color-surf2);
    border: 1px solid var(--color-bord);
    border-radius: 8px;
    padding: 1rem;
}

/* ── Progress bar ── */
.prog-wrap {
    background: var(--color-bord);
    border-radius: 4px;
    height: 10px;
    overflow: hidden;
    margin: 5px 0 3px 0;
}
.prog-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, var(--idu-red), #FF3B5C);
}
.prog-fill-green {
    background: linear-gradient(90deg, var(--success), #56d364);
}

/* ── Table styling ── */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.80rem;
    letter-spacing: 0.04em;
    border-radius: 6px;
    transition: all 0.15s;
}
.stButton > button[kind="primary"] {
    background: var(--idu-red) !important;
    border-color: var(--idu-red) !important;
    color: #fff !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--idu-red-lt) !important;
}

/* ── Headings ── */
h1,h2,h3 { font-weight: 600; color: var(--color-text); }
h3 { border-bottom: 1px solid var(--color-bord); padding-bottom: 0.35rem; margin-bottom: 0.9rem; }

/* ── Info / warn boxes ── */
.info-box {
    background: rgba(56,139,253,0.08);
    border-left: 3px solid var(--info);
    border-radius: 0 6px 6px 0;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    color: #c9d1d9;
    font-size: 0.87rem;
}
.warn-box {
    background: rgba(210,153,34,0.08);
    border-left: 3px solid var(--warning);
    border-radius: 0 6px 6px 0;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    color: #c9d1d9;
    font-size: 0.87rem;
}

/* ── Light mode overrides ── */
[data-theme="light"] .stApp               { background: #f6f8fa; color: #24292f; }
[data-theme="light"] .kpi-card            { background: #ffffff !important; border-color: #d0d7de !important; }
[data-theme="light"] .kpi-label           { color: #57606a !important; }
[data-theme="light"] .kpi-value           { color: #24292f !important; }
[data-theme="light"] .kpi-sub             { color: #6e7781 !important; }
[data-theme="light"] .nav-category        { color: var(--idu-red) !important; border-top-color: #d0d7de !important; }
[data-theme="light"] .badge-borrador      { background: #f6f8fa; color: #57606a; border: 1px solid #d0d7de; }
[data-theme="light"] .badge-revisado      { background: #dafbe1; color: #116329; }
[data-theme="light"] .badge-aprobado      { background: #ddf4ff; color: #0550ae; }
[data-theme="light"] .badge-devuelto      { background: #ffebe9; color: #cf222e; }
[data-theme="light"] .apr-panel           { background: #f6f8fa; border-color: #d0d7de; }
[data-theme="light"] section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #d0d7de !important;
}
[data-theme="light"] .info-box { background: rgba(56,139,253,0.06); color: #24292f; }
[data-theme="light"] .warn-box { background: rgba(210,153,34,0.06); color: #24292f; }
[data-theme="light"] .sec-title { border-bottom-color: #d0d7de; }

hr { border-color: var(--color-bord); }
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


def fmt_cop(val):
    """Formatea valor en pesos colombianos."""
    v = safe_float(val)
    if v is None:
        return "—"
    if abs(v) >= 1_000_000_000:
        return f"${v/1_000_000_000:.2f} B"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f} M"
    return f"${v:,.0f}"


def badge(estado: str) -> str:
    cls = {
        'BORRADOR': 'badge-borrador',
        'REVISADO': 'badge-revisado',
        'APROBADO': 'badge-aprobado',
        'DEVUELTO': 'badge-devuelto',
    }.get(str(estado).upper(), 'badge-borrador')
    return f'<span class="badge {cls}">{estado}</span>'


def tipo_tag(tipo: str, label: str = None) -> str:
    cls = {
        'general':    'tipo-general',
        'clima':      'tipo-clima',
        'maquinaria': 'tipo-maquinaria',
        'personal':   'tipo-personal',
        'sst':        'tipo-sst',
        'social':     'tipo-social',
        'ambiental':  'tipo-ambiental',
        'pmt':        'tipo-pmt',
        'cantidades': 'tipo-cant',
    }.get(tipo.lower(), 'tipo-general')
    return f'<span class="tipo-tag {cls}">{label or tipo}</span>'


def kpi(label, value, sub="", accent="", card_cls=""):
    val_cls = f"kpi-value {accent}" if accent else "kpi-value"
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card {card_cls}">
        <div class="kpi-label">{label}</div>
        <div class="{val_cls}">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def sec_title(text):
    st.markdown(f'<div class="sec-title">{text}</div>', unsafe_allow_html=True)


def prog_bar(pct, color="red"):
    cls = "prog-fill-green" if color == "green" else "prog-fill"
    safe_pct = min(max(float(pct or 0), 0), 100)
    st.markdown(f"""
    <div class="prog-wrap">
        <div class="{cls}" style="width:{safe_pct}%;"></div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# DATA LOADERS
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_contrato():
    sb = get_supabase()
    r  = sb.table('contratos').select('*').eq('id', 'IDU-1556-2025').execute()
    return r.data[0] if r.data else {}


@st.cache_data(ttl=300)
def load_prorrogas():
    sb = get_supabase()
    r  = sb.table('contratos_prorrogas').select('*').eq('contrato_id', 'IDU-1556-2025').order('numero').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_adiciones():
    sb = get_supabase()
    r  = sb.table('contratos_adiciones').select('*').eq('contrato_id', 'IDU-1556-2025').order('numero').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=60)
def load_cantidades(estados=None, fecha_ini=None, fecha_fin=None):
    sb    = get_supabase()
    q     = sb.table('registros_cantidades').select('*')
    if estados:
        q = q.in_('estado', estados)
    if fecha_ini:
        q = q.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        q = q.lte('fecha_creacion', fecha_fin + 'T23:59:59')
    r = q.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=60)
def load_componentes(componente=None, estados=None, fecha_ini=None, fecha_fin=None):
    sb = get_supabase()
    q  = sb.table('registros_componentes').select('*')
    if estados:
        q = q.in_('estado', estados)
    if fecha_ini:
        q = q.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        q = q.lte('fecha_creacion', fecha_fin + 'T23:59:59')
    r = q.order('fecha_creacion', desc=True).execute()
    df = pd.DataFrame(r.data) if r.data else pd.DataFrame()
    if componente and not df.empty and 'componente' in df.columns:
        df = df[df['componente'].str.upper().str.contains(componente.upper(), na=False)]
    return df


@st.cache_data(ttl=60)
def load_reporte_diario(estados=None, fecha_ini=None, fecha_fin=None):
    sb = get_supabase()
    q  = sb.table('registros_reporte_diario').select('*')
    if estados:
        q = q.in_('estado', estados)
    if fecha_ini:
        q = q.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        q = q.lte('fecha_creacion', fecha_fin + 'T23:59:59')
    r = q.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_bd_personal(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('bd_personal_obra').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_bd_clima(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('bd_condicion_climatica').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_bd_maquinaria(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('bd_maquinaria_obra').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_bd_sst(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('bd_sst_ambiental').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_fotos_cantidades(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('rf_cantidades').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_fotos_componentes(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('rf_componentes').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_fotos_reporte(folios: tuple):
    if not folios:
        return pd.DataFrame()
    sb = get_supabase()
    r  = sb.table('rf_reporte_diario').select('*').in_('folio', list(folios)).execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_presupuesto():
    sb = get_supabase()
    r  = sb.table('presupuesto_bd').select('*').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=300)
def load_presupuesto_componentes():
    sb = get_supabase()
    r  = sb.table('presupuesto_componentes_bd').select('*').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


def clear_cache():
    st.cache_data.clear()


# ══════════════════════════════════════════════════════════════
# FLUJO DE APROBACIÓN — configuración por rol
# ══════════════════════════════════════════════════════════════

# (rol) → (estados_visibles, estado_al_aprobar, campo_cant, campo_obs, campo_apr, campo_fecha, campo_estado_rol)
APR_CFG = {
    'inspector':   (None,                        None,       None),
    'obra':        (None,                        None,       None),
    'residente':   (['BORRADOR', 'DEVUELTO'],    'REVISADO', {
        'campo_cant':   'cant_residente',
        'campo_obs':    'obs_residente',
        'campo_apr':    'aprobado_residente',
        'campo_fecha':  'fecha_residente',
        'campo_estado': 'estado_residente',
    }),
    'coordinador': (['BORRADOR', 'DEVUELTO'],    'REVISADO', {
        'campo_cant':   'cant_residente',
        'campo_obs':    'obs_residente',
        'campo_apr':    'aprobado_residente',
        'campo_fecha':  'fecha_residente',
        'campo_estado': 'estado_residente',
    }),
    'interventor': (['REVISADO'],                'APROBADO', {
        'campo_cant':   'cant_interventor',
        'campo_obs':    'obs_interventor',
        'campo_apr':    'aprobado_interventor',
        'campo_fecha':  'fecha_interventor',
        'campo_estado': 'estado_interventor',
    }),
    'supervisor':  (None,                        None,       None),
    'admin':       (['BORRADOR','DEVUELTO','REVISADO'], 'APROBADO', {
        'campo_cant':   'cant_interventor',
        'campo_obs':    'obs_interventor',
        'campo_apr':    'aprobado_interventor',
        'campo_fecha':  'fecha_interventor',
        'campo_estado': 'estado_interventor',
    }),
}


def render_panel_aprobacion(tabla: str, reg: dict, perfil: dict, con_cantidad: bool = True):
    """Renders approval/return panel for a single record.
    tabla: 'registros_cantidades' | 'registros_componentes' | 'registros_reporte_diario'
    """
    rol = perfil['rol']
    cfg = APR_CFG.get(rol, (None, None, None))
    estados_vis, estado_nuevo, campos = cfg
    if not campos:
        return  # read-only role

    estado_actual = str(reg.get('estado', '')).upper()
    if estados_vis and estado_actual not in estados_vis:
        st.caption(f"Estado actual: {estado_actual} — sin acción disponible para tu rol")
        return

    reg_id = str(reg.get('id', ''))
    with st.container():
        st.markdown('<div class="apr-panel">', unsafe_allow_html=True)
        st.markdown("**Validación / Revisión**")

        campo_cant  = campos['campo_cant']
        campo_obs   = campos['campo_obs']
        campo_apr   = campos['campo_apr']
        campo_fecha = campos['campo_fecha']
        campo_estado_rol = campos['campo_estado']

        # Cantidad (solo si aplica: cantidades y componentes)
        cant_val = None
        if con_cantidad:
            cant_def = safe_float(reg.get(campo_cant)) or safe_float(reg.get('cantidad')) or 0.0
            cant_val = st.number_input(
                "Cantidad validada",
                value=float(cant_def),
                step=0.01,
                key=f"cant_{tabla[:4]}_{reg_id}"
            )

        obs_val = st.text_area(
            "Observación",
            key=f"obs_{tabla[:4]}_{reg_id}",
            height=75,
            placeholder="Opcional para aprobar · Obligatoria para devolver",
            value=str(reg.get(campo_obs) or '')
        )

        col_a, col_d = st.columns(2)
        with col_a:
            if st.button(
                "✅ Aprobar",
                key=f"apr_{tabla[:4]}_{reg_id}",
                use_container_width=True,
                type="primary"
            ):
                try:
                    upd = {
                        'estado':        estado_nuevo,
                        campo_estado_rol: 'aprobado',
                        campo_apr:       perfil['id'],
                        campo_fecha:     datetime.now().isoformat(),
                    }
                    if con_cantidad and cant_val is not None:
                        upd[campo_cant] = cant_val
                    if obs_val:
                        upd[campo_obs] = obs_val
                    get_supabase().table(tabla).update(upd).eq('id', reg_id).execute()
                    clear_cache()
                    st.success("✅ Registro aprobado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al aprobar: {e}")

        with col_d:
            if st.button(
                "↩️ Devolver",
                key=f"dev_{tabla[:4]}_{reg_id}",
                use_container_width=True
            ):
                if not obs_val or not obs_val.strip():
                    st.error("Escribe una observación para devolver")
                else:
                    try:
                        get_supabase().table(tabla).update({
                            'estado':        'DEVUELTO',
                            campo_estado_rol: 'devuelto',
                            campo_obs:       obs_val,
                            campo_fecha:     datetime.now().isoformat(),
                        }).eq('id', reg_id).execute()
                        clear_cache()
                        st.warning("↩️ Devuelto")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al devolver: {e}")

        # Mostrar historial de revisiones si ya hay datos
        prev_obs_res = reg.get('obs_residente')
        prev_obs_int = reg.get('obs_interventor')
        if prev_obs_res:
            st.markdown(f'<div class="info-box">📋 Obs. residente: {prev_obs_res}</div>', unsafe_allow_html=True)
        if prev_obs_int:
            st.markdown(f'<div class="warn-box">📋 Obs. interventor: {prev_obs_int}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def login():
    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.68rem;
                        letter-spacing:0.16em; color:#C8102E; text-transform:uppercase;
                        margin-bottom:0.3rem;">
                Bitácora Digital de Obra
            </div>
            <div style="font-size:2rem; font-weight:700; color:#e6edf3; margin-bottom:0.1rem;">
                BDO · IDU-1556-2025
            </div>
            <div style="font-size:0.83rem; color:#6e7681;">
                Contrato Grupo 4 · Mártires · San Cristóbal · Rafael Uribe Uribe · Santafé · Antonio Nariño
            </div>
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
# SIDEBAR
# ══════════════════════════════════════════════════════════════

ROL_LABELS = {
    'inspector':   '📋 Inspector de Obra',
    'obra':        '🔧 Personal de Obra',
    'residente':   '✏️ Residente de Obra',
    'coordinador': '📐 Coordinador',
    'interventor': '✅ Interventor',
    'supervisor':  '👁️ Supervisor IDU',
    'admin':       '⚙️ Administrador',
}

NAV_ACCESS = {
    "Estado Actual":            ['inspector','obra','residente','coordinador','interventor','supervisor','admin'],
    "Anotaciones Diario":       ['inspector','obra','residente','coordinador','interventor','supervisor','admin'],
    "Reporte Cantidades":       ['residente','coordinador','interventor','supervisor','admin'],
    "Mapa Ejecución":           ['residente','coordinador','interventor','supervisor','admin'],
    "Seguimiento Presupuesto":  ['residente','coordinador','interventor','supervisor','admin'],
    "Componente Social":        ['residente','coordinador','interventor','supervisor','admin'],
    "Componente Ambiental-SST": ['residente','coordinador','interventor','supervisor','admin'],
    "Componente PMT":           ['residente','coordinador','interventor','supervisor','admin'],
    "Generar Informe":          ['residente','coordinador','interventor','supervisor','admin'],
}

CATEGORIES = {
    "General": ["Estado Actual"],
    "Reportes": ["Anotaciones Diario", "Reporte Cantidades", "Mapa Ejecución", "Seguimiento Presupuesto"],
    "Componentes Transversales": ["Componente Social", "Componente Ambiental-SST", "Componente PMT"],
    "Informe": ["Generar Informe"],
}

NAV_ICONS = {
    "Estado Actual":            "◈",
    "Anotaciones Diario":       "◉",
    "Reporte Cantidades":       "◈",
    "Mapa Ejecución":           "◉",
    "Seguimiento Presupuesto":  "◫",
    "Componente Social":        "◈",
    "Componente Ambiental-SST": "◉",
    "Componente PMT":           "◫",
    "Generar Informe":          "◈",
}


def sidebar(perfil):
    rol = perfil['rol']

    with st.sidebar:
        # ── Header usuario ──────────────────────────────────
        st.markdown(f"""
        <div style="padding:0.8rem 0 0.6rem; border-bottom:1px solid #1c2333; margin-bottom:0.4rem;">
            <div style="font-size:0.68rem; color:#6e7681; font-family:'IBM Plex Mono',monospace;
                        text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.2rem;">
                {ROL_LABELS.get(rol, rol)}
            </div>
            <div style="font-size:0.98rem; font-weight:600; color:#e6edf3;">{perfil['nombre']}</div>
            <div style="font-size:0.76rem; color:#8b949e;">{perfil.get('empresa','')}</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Counters rápidos ──────────────────────────────
        try:
            df_q = load_cantidades()
            if not df_q.empty:
                total = len(df_q)
                apr   = len(df_q[df_q['estado'] == 'APROBADO'])
                dev   = len(df_q[df_q['estado'] == 'DEVUELTO'])
                pend  = len(df_q[df_q['estado'].isin(['BORRADOR', 'REVISADO'])])
                st.markdown(f"""
                <div style="display:flex; gap:5px; margin-bottom:0.7rem; flex-wrap:wrap;">
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                                 background:#161b22;border:1px solid #21262d;border-radius:3px;
                                 padding:2px 7px;color:#8b949e;">Total {total}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                                 background:#1a3255;border-radius:3px;padding:2px 7px;color:#79c0ff;">
                        ✅ {apr}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                                 background:#2d2a1e;border-radius:3px;padding:2px 7px;color:#e3b341;">
                        ⏳ {pend}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
                                 background:#3d1e1e;border-radius:3px;padding:2px 7px;color:#f85149;">
                        ↩️ {dev}</span>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

        # ── Navegación ──────────────────────────────────────
        opciones = []
        for cat, pages in CATEGORIES.items():
            accesibles = [p for p in pages if rol in NAV_ACCESS.get(p, [])]
            if not accesibles:
                continue
            st.markdown(f'<div class="nav-category">{cat}</div>', unsafe_allow_html=True)
            for page in accesibles:
                opciones.append(page)
                icon     = NAV_ICONS.get(page, "◈")
                is_sel   = st.session_state.get('current_page') == page
                bg_style = "background:#1c2333; border-radius:5px;" if is_sel else ""
                if st.button(
                    f"{icon}  {page}",
                    key=f"nav_{page}",
                    use_container_width=True,
                ):
                    st.session_state['current_page'] = page
                    st.rerun()

        if not st.session_state.get('current_page') and opciones:
            st.session_state['current_page'] = opciones[0]

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Actualizar", use_container_width=True):
                clear_cache()
                st.rerun()
        with c2:
            if st.button("🚪 Salir", use_container_width=True):
                logout()

    return st.session_state.get('current_page', opciones[0] if opciones else "Estado Actual")


# ══════════════════════════════════════════════════════════════
# 1. ESTADO ACTUAL
# ══════════════════════════════════════════════════════════════

def page_estado_actual():
    st.markdown("### Estado Actual del Contrato")

    contrato  = load_contrato()
    df_pro    = load_prorrogas()
    df_adi    = load_adiciones()

    if not contrato:
        st.info("Sin datos de contrato. Verifica la tabla `contratos` en Supabase.")
        contrato = {
            'id': 'IDU-1556-2025',
            'nombre': 'Contrato IDU-1556-2025 Grupo 4',
            'contratista': 'URBACON SAS',
            'intrventoria': 'CONSORCIO INTERCONSERVACION',
            'supervisor_idu': 'IDU',
            'fecha_inicio': '2025-12-26',
            'fecha_fin': '2028-02-26',
            'valor_contrato': 40704606199,
            'valor_actual': 40704606199,
            'prorrogas': 0,
            'adiciones': 0,
            'plazo_actual': '2028-02-26',
        }

    # ── Cálculos de tiempo ──────────────────────────────────
    fi_str   = str(contrato.get('fecha_inicio') or '2025-01-01')[:10]
    ff_str   = str(contrato.get('fecha_fin') or '2026-01-01')[:10]
    pa_str   = str(contrato.get('plazo_actual') or ff_str)[:10]

    fecha_inicio   = datetime.strptime(fi_str, '%Y-%m-%d').date()
    fecha_fin_orig = datetime.strptime(ff_str, '%Y-%m-%d').date()
    fecha_fin_act  = datetime.strptime(pa_str, '%Y-%m-%d').date()

    hoy          = date.today()
    dias_trans   = (hoy - fecha_inicio).days
    plazo_orig   = (fecha_fin_orig - fecha_inicio).days
    plazo_total  = (fecha_fin_act - fecha_inicio).days
    dias_rest    = max((fecha_fin_act - hoy).days, 0)
    pct_tiempo   = round(min(dias_trans / plazo_total * 100, 100), 1) if plazo_total > 0 else 0

    val_ini  = safe_float(contrato.get('valor_contrato')) or 0
    val_act  = safe_float(contrato.get('valor_actual'))   or val_ini
    n_pro    = int(contrato.get('prorrogas')  or 0)
    n_adi    = int(contrato.get('adiciones')  or 0)

    # ── Identificación del Contrato ──────────────────────────
    sec_title("Identificación del Contrato")
    ci1, ci2 = st.columns(2)

    with ci1:
        st.markdown(f"""
        <div class="kpi-card kpi-card-red">
            <div class="kpi-label">Número de Contrato</div>
            <div class="kpi-value kpi-idu">{contrato.get('id','—')}</div>
            <div class="kpi-sub">{contrato.get('nombre','')}</div>
        </div>
        """, unsafe_allow_html=True)
        kpi("Contratista",    contrato.get('contratista','—'))
        kpi("Interventoría",  contrato.get('intrventoria','—'))

    with ci2:
        kpi("Supervisor IDU", contrato.get('supervisor_idu','—'))
        kpi("Fecha de Inicio",
            fecha_inicio.strftime('%d/%m/%Y'),
            sub=f"Fecha fin original: {fecha_fin_orig.strftime('%d/%m/%Y')}")
        kpi("Fecha Fin Actualizada",
            fecha_fin_act.strftime('%d/%m/%Y'),
            sub=f"{n_pro} prórroga(s) aplicada(s)",
            accent="kpi-warn" if n_pro > 0 else "")

    st.divider()

    # ── Ejecución del Plazo ──────────────────────────────────
    sec_title("Ejecución del Plazo")
    ct1, ct2, ct3, ct4 = st.columns(4)

    accent_t = "kpi-danger" if pct_tiempo > 85 else ("kpi-warn" if pct_tiempo > 60 else "kpi-accent")
    with ct1: kpi("Días Transcurridos", str(dias_trans),
                  sub=f"{pct_tiempo}% del plazo vigente", accent=accent_t)
    with ct2: kpi("Días Restantes",     str(dias_rest))
    with ct3: kpi("Plazo Original",     f"{plazo_orig} días",
                  sub=fecha_fin_orig.strftime('%d/%m/%Y'))
    with ct4: kpi("Prórrogas",          str(n_pro),
                  sub=f"+{(fecha_fin_act - fecha_fin_orig).days} días totales",
                  accent="kpi-warn" if n_pro > 0 else "")

    # Barra de progreso temporal
    fig_t = go.Figure(go.Bar(
        x=[pct_tiempo, 100 - pct_tiempo],
        y=["Plazo"],
        orientation='h',
        marker_color=['#C8102E', '#21262d'],
        text=[f"  {pct_tiempo}% transcurrido", f"  {100-pct_tiempo:.1f}% restante"],
        textposition='inside',
        textfont=dict(family="IBM Plex Mono", size=11, color="white"),
        hoverinfo='skip',
    ))
    fig_t.update_layout(
        height=60, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, barmode='stack',
        xaxis=dict(showticklabels=False, range=[0,100], showgrid=False),
        yaxis=dict(showticklabels=False, showgrid=False),
    )
    st.plotly_chart(fig_t, use_container_width=True, config={'displayModeBar': False})

    st.divider()

    # ── Ejecución Financiera ─────────────────────────────────
    sec_title("Ejecución Financiera")
    cf1, cf2, cf3 = st.columns(3)

    with cf1:
        kpi("Valor Inicial del Contrato", fmt_cop(val_ini),
            sub=f"${val_ini:,.0f}", card_cls="kpi-card-blue")
    with cf2:
        diff = val_act - val_ini
        kpi("Valor Actualizado",   fmt_cop(val_act),
            sub=f"Δ {fmt_cop(diff)} por {n_adi} adición(es)",
            accent="kpi-warn" if diff != 0 else "",
            card_cls="kpi-card-warn")
    with cf3:
        kpi("Adiciones / Modificaciones", str(n_adi),
            sub=f"Última: {fmt_cop(val_act)}", card_cls="kpi-card-green")

    st.divider()

    # ── Seguimiento de Prórrogas ─────────────────────────────
    sec_title("Seguimiento de Prórrogas")

    if df_pro.empty:
        st.markdown('<div class="info-box">Sin prórrogas registradas para este contrato.</div>', unsafe_allow_html=True)
    else:
        cols_pro = ['numero', 'plazo_dias', 'fecha_fin', 'fecha_firma', 'observaciones']
        cols_pro = [c for c in cols_pro if c in df_pro.columns]
        st.dataframe(
            df_pro[cols_pro],
            hide_index=True,
            use_container_width=True,
            column_config={
                'numero':      st.column_config.NumberColumn('No.', format="%d"),
                'plazo_dias':  st.column_config.NumberColumn('Días adicionados', format="%d"),
                'fecha_fin':   st.column_config.DateColumn('Nueva fecha fin', format="DD/MM/YYYY"),
                'fecha_firma': st.column_config.DateColumn('Fecha firma', format="DD/MM/YYYY"),
                'observaciones': st.column_config.TextColumn('Observaciones'),
            }
        )

    st.divider()

    # ── Seguimiento de Adiciones ─────────────────────────────
    sec_title("Seguimiento de Adiciones Presupuestales")

    if df_adi.empty:
        st.markdown('<div class="info-box">Sin adiciones presupuestales registradas para este contrato.</div>', unsafe_allow_html=True)
    else:
        cols_adi = ['numero', 'adicion', 'valor_actual', 'fecha_firma', 'observaciones']
        cols_adi = [c for c in cols_adi if c in df_adi.columns]
        st.dataframe(
            df_adi[cols_adi],
            hide_index=True,
            use_container_width=True,
            column_config={
                'numero':       st.column_config.NumberColumn('No.',   format="%d"),
                'adicion':      st.column_config.NumberColumn('Adición ($)', format="$%,.0f"),
                'valor_actual': st.column_config.NumberColumn('Valor Acumulado ($)', format="$%,.0f"),
                'fecha_firma':  st.column_config.DateColumn('Fecha firma', format="DD/MM/YYYY"),
                'observaciones': st.column_config.TextColumn('Observaciones'),
            }
        )


# ══════════════════════════════════════════════════════════════
# 2. ANOTACIONES DIARIO
# ══════════════════════════════════════════════════════════════

def page_anotaciones_diario(perfil):
    rol = perfil['rol']
    st.markdown("### Anotaciones — Reporte Diario")

    # ── Filtros ──────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 3])
    with fc1: fi = st.date_input("Desde", value=date.today()-timedelta(days=15), key="rd_fi")
    with fc2: ff = st.date_input("Hasta", value=date.today(), key="rd_ff")
    with fc3:
        cfg = APR_CFG.get(rol, (None, None, None))
        est_vis = cfg[0]
        opciones_est = est_vis if est_vis else ["BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
        estado_f = st.selectbox("Estado", ["Todos"] + opciones_est, key="rd_est")
    with fc4: buscar = st.text_input("🔍 Folio / Observación", key="rd_bus")

    estados_q = None if estado_f == "Todos" else [estado_f]

    df = load_reporte_diario(estados=estados_q,
                             fecha_ini=fi.isoformat(),
                             fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = (
            df.get('folio', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False) |
            df.get('observaciones', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False) |
            df.get('usuario_qfield', pd.Series(dtype=str)).astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("No hay reportes diarios para los filtros seleccionados.")
        return

    # ── Indicadores acumulados ──────────────────────────────
    sec_title("Indicadores del Período")
    folios = tuple(df['folio'].dropna().tolist()) if 'folio' in df.columns else ()

    col_i = st.columns(5)
    with col_i[0]: kpi("Total Reportes",  str(len(df)))
    with col_i[1]: kpi("Aprobados",  str(len(df[df['estado']=='APROBADO']))  if 'estado' in df else "0", accent="kpi-info")
    with col_i[2]: kpi("Revisados",  str(len(df[df['estado']=='REVISADO']))  if 'estado' in df else "0", accent="kpi-accent")
    with col_i[3]: kpi("Borradores", str(len(df[df['estado']=='BORRADOR']))  if 'estado' in df else "0", accent="kpi-warn")
    with col_i[4]: kpi("Devueltos",  str(len(df[df['estado']=='DEVUELTO']))  if 'estado' in df else "0", accent="kpi-danger")

    # Cargar sub-datos en batch
    df_personal   = load_bd_personal(folios)   if folios else pd.DataFrame()
    df_clima      = load_bd_clima(folios)       if folios else pd.DataFrame()
    df_maquinaria = load_bd_maquinaria(folios)  if folios else pd.DataFrame()
    df_sst        = load_bd_sst(folios)         if folios else pd.DataFrame()
    df_fotos      = load_fotos_reporte(folios)  if folios else pd.DataFrame()

    # KPIs de personal si hay datos
    if not df_personal.empty:
        cols_num = ['inspectores','personal_operativo','personal_boal','personal_transito']
        totales = {c: int(pd.to_numeric(df_personal[c], errors='coerce').fillna(0).sum())
                   for c in cols_num if c in df_personal.columns}
        if totales:
            st.markdown("**Personal acumulado en el período:**")
            p_cols = st.columns(len(totales))
            for i, (k, v) in enumerate(totales.items()):
                with p_cols[i]:
                    kpi(k.replace('_', ' ').title(), str(v), accent="kpi-info")

    st.divider()
    sec_title(f"Reportes ({len(df)})")

    # ── Lista de reportes ───────────────────────────────────
    for _, reg in df.iterrows():
        folio      = str(reg.get('folio', '—'))
        est_actual = str(reg.get('estado', ''))
        fecha_rep  = str(reg.get('fecha_reporte', reg.get('fecha', '')))[:10]
        usuario    = str(reg.get('usuario_qfield', '—'))

        titulo = f"**{folio}** · {fecha_rep} · {usuario}"

        with st.expander(titulo, expanded=False):
            # Tabs para cada sub-tipo
            tabs_labels = ["📋 General"]
            if not df_clima.empty and folio in df_clima.get('folio', pd.Series()).tolist():
                tabs_labels.append("🌤️ Clima")
            if not df_maquinaria.empty and folio in df_maquinaria.get('folio', pd.Series()).tolist():
                tabs_labels.append("🚜 Maquinaria")
            if not df_personal.empty and folio in df_personal.get('folio', pd.Series()).tolist():
                tabs_labels.append("👷 Personal")
            if not df_sst.empty and folio in df_sst.get('folio', pd.Series()).tolist():
                tabs_labels.append("⚠️ SST")

            tabs = st.tabs(tabs_labels)
            tab_idx = 0

            # Tab General
            with tabs[tab_idx]:
                cg1, cg2 = st.columns([2.5, 1.2])
                with cg1:
                    st.markdown(f"""
                    <div style="display:flex; gap:6px; align-items:center; margin-bottom:0.7rem;">
                        {badge(est_actual)}
                        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:#6e7681;">
                            {fecha_rep}
                        </span>
                        {tipo_tag('general','Reporte Diario')}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"**Inspector/Usuario:** {usuario}")
                    if reg.get('observaciones'):
                        st.markdown(f'<div class="info-box">📝 {reg["observaciones"]}</div>', unsafe_allow_html=True)

                    # Fotos
                    fotos_reg = df_fotos[df_fotos['folio'] == folio] if not df_fotos.empty and 'folio' in df_fotos.columns else pd.DataFrame()
                    if not fotos_reg.empty:
                        urls = fotos_reg['foto_url'].dropna().tolist()
                        if urls:
                            st.markdown("**📷 Registro fotográfico**")
                            f_cols = st.columns(min(len(urls), 4))
                            for i, url in enumerate(urls[:4]):
                                with f_cols[i]:
                                    st.image(url, use_column_width=True)
                    else:
                        st.caption("Sin registro fotográfico")

                with cg2:
                    render_panel_aprobacion(
                        tabla='registros_reporte_diario',
                        reg=dict(reg),
                        perfil=perfil,
                        con_cantidad=False
                    )
                tab_idx += 1

            # Tab Clima
            if "🌤️ Clima" in tabs_labels:
                with tabs[tab_idx]:
                    sub = df_clima[df_clima['folio'] == folio]
                    if sub.empty:
                        st.caption("Sin datos climáticos")
                    else:
                        for _, r in sub.iterrows():
                            st.markdown(f"""
                            {tipo_tag('clima','Condición Climática')}
                            <br>**Estado:** {r.get('estado_clima','—')} &nbsp;|&nbsp;
                            **Hora:** {str(r.get('hora','—'))[:5]} &nbsp;|&nbsp;
                            **Obs:** {r.get('observaciones','—')}
                            """, unsafe_allow_html=True)
                tab_idx += 1

            # Tab Maquinaria
            if "🚜 Maquinaria" in tabs_labels:
                with tabs[tab_idx]:
                    sub = df_maquinaria[df_maquinaria['folio'] == folio]
                    if sub.empty:
                        st.caption("Sin datos de maquinaria")
                    else:
                        maq_cols = ['operarios','volquetas','vibrocompactador','equipos_especiales',
                                    'minicargador','ruteadora','compresor','retrocargador',
                                    'extendedora_asfalto','compactador_neumatico','observaciones']
                        maq_cols = [c for c in maq_cols if c in sub.columns]
                        st.dataframe(sub[maq_cols], hide_index=True, use_container_width=True)
                tab_idx += 1

            # Tab Personal
            if "👷 Personal" in tabs_labels:
                with tabs[tab_idx]:
                    sub = df_personal[df_personal['folio'] == folio]
                    if sub.empty:
                        st.caption("Sin datos de personal")
                    else:
                        pers_cols = ['inspectores','personal_operativo','personal_boal','personal_transito']
                        pers_cols = [c for c in pers_cols if c in sub.columns]
                        for _, r in sub.iterrows():
                            p_cs = st.columns(len(pers_cols))
                            for i, col in enumerate(pers_cols):
                                with p_cs[i]:
                                    st.metric(col.replace('_',' ').title(), int(r.get(col, 0) or 0))
                tab_idx += 1

            # Tab SST
            if "⚠️ SST" in tabs_labels:
                with tabs[tab_idx]:
                    sub = df_sst[df_sst['folio'] == folio]
                    if sub.empty:
                        st.caption("Sin datos SST")
                    else:
                        sst_cols = ['botiquin','kit_antiderrames','punto_hidratacion',
                                    'punto_ecologico','extintor','observaciones']
                        sst_cols = [c for c in sst_cols if c in sub.columns]
                        for _, r in sub.iterrows():
                            num_cols = [c for c in sst_cols if c != 'observaciones']
                            s_cs = st.columns(len(num_cols))
                            for i, col in enumerate(num_cols):
                                with s_cs[i]:
                                    st.metric(col.replace('_',' ').title(), int(r.get(col, 0) or 0))
                            if r.get('observaciones'):
                                st.markdown(f'<div class="warn-box">⚠️ {r["observaciones"]}</div>',
                                            unsafe_allow_html=True)
                tab_idx += 1


# ══════════════════════════════════════════════════════════════
# 3. REPORTE CANTIDADES
# ══════════════════════════════════════════════════════════════

def page_reporte_cantidades(perfil):
    rol = perfil['rol']
    st.markdown("### Reporte de Cantidades de Obra")

    # ── Filtros ──────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    with fc1: fi = st.date_input("Desde", value=date.today()-timedelta(days=30), key="rc_fi")
    with fc2: ff = st.date_input("Hasta", value=date.today(), key="rc_ff")
    with fc3:
        cfg = APR_CFG.get(rol, (None, None, None))
        opciones_est = cfg[0] if cfg[0] else ["BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
        estado_f = st.selectbox("Estado", ["Todos"] + opciones_est, key="rc_est")

    fc4, fc5, fc6 = st.columns(3)
    with fc4: civ_f   = st.text_input("🔍 CIV",      key="rc_civ")
    with fc5: tramo_f = st.text_input("🔍 Tramo",    key="rc_tramo")
    with fc6: buscar  = st.text_input("🔍 Búsqueda", key="rc_bus",
                                      placeholder="folio / ítem / actividad")

    estados_q = None if estado_f == "Todos" else [estado_f]
    df = load_cantidades(estados=estados_q,
                         fecha_ini=fi.isoformat(),
                         fecha_fin=ff.isoformat())

    # Filtros en Python
    if not df.empty:
        if civ_f:
            df = df[df.get('civ', pd.Series(dtype=str)).astype(str).str.contains(civ_f, case=False, na=False)]
        if tramo_f:
            df = df[df.get('id_tramo', pd.Series(dtype=str)).astype(str).str.contains(tramo_f, case=False, na=False) |
                    df.get('tramo_descripcion', pd.Series(dtype=str)).astype(str).str.contains(tramo_f, case=False, na=False)]
        if buscar:
            mask = pd.Series(False, index=df.index)
            for col in ['folio','item_pago','item_descripcion','tipo_actividad','capitulo','usuario_qfield']:
                if col in df.columns:
                    mask |= df[col].astype(str).str.contains(buscar, case=False, na=False)
            df = df[mask]

    if df.empty:
        st.info("No hay registros de cantidades para los filtros seleccionados.")
        return

    # ── Indicadores acumulados ──────────────────────────────
    sec_title("Indicadores")
    mi1, mi2, mi3, mi4, mi5 = st.columns(5)
    with mi1: kpi("Total Registros", str(len(df)))
    with mi2: kpi("Aprobados",  str(len(df[df['estado']=='APROBADO']))  if 'estado' in df else "0", accent="kpi-info")
    with mi3: kpi("Revisados",  str(len(df[df['estado']=='REVISADO']))  if 'estado' in df else "0", accent="kpi-accent")
    with mi4: kpi("Borradores", str(len(df[df['estado'].isin(['BORRADOR','DEVUELTO'])]))  if 'estado' in df else "0", accent="kpi-warn")
    with mi5:
        cant_total = df['cantidad'].apply(safe_float).sum() if 'cantidad' in df.columns else 0
        kpi("Cant. Reportada (suma)", f"{cant_total:,.2f}", accent="kpi-idu")

    # Cantidad aprobada
    if 'cant_interventor' in df.columns:
        cant_apr = df[df['estado']=='APROBADO']['cant_interventor'].apply(safe_float).sum()
        st.markdown(f'<div class="info-box">✅ Cantidad acumulada aprobada: <strong>{cant_apr:,.2f}</strong></div>',
                    unsafe_allow_html=True)

    st.divider()

    # ── Tabla principal ──────────────────────────────────────
    sec_title(f"Registros ({len(df)})")

    show_cols = ['folio','usuario_qfield','id_tramo','civ','tipo_actividad','capitulo',
                 'item_pago','item_descripcion','unidad','cantidad','cant_residente',
                 'cant_interventor','estado','fecha_creacion']
    show_cols = [c for c in show_cols if c in df.columns]

    st.dataframe(
        df[show_cols],
        hide_index=True,
        use_container_width=True,
        column_config={
            'cantidad':          st.column_config.NumberColumn('Cant. Inspector', format="%.3f"),
            'cant_residente':    st.column_config.NumberColumn('Cant. Residente', format="%.3f"),
            'cant_interventor':  st.column_config.NumberColumn('Cant. Interventor', format="%.3f"),
            'fecha_creacion':    st.column_config.DatetimeColumn('Fecha', format="DD/MM/YY HH:mm"),
        }
    )

    # CSV export
    csv = df[show_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name=f"Cantidades_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    st.divider()

    # ── Detalle con fotos y aprobación ──────────────────────
    sec_title("Detalle y Aprobación")

    cfg = APR_CFG.get(rol, (None, None, None))
    est_vis = cfg[0]
    if est_vis:
        df_acc = df[df['estado'].isin(est_vis)] if 'estado' in df.columns else df
    else:
        df_acc = df

    if df_acc.empty:
        st.markdown('<div class="info-box">✅ Sin registros pendientes para tu rol.</div>', unsafe_allow_html=True)
        df_acc = df  # show all for read-only

    folios = tuple(df_acc['folio'].dropna().unique().tolist()) if 'folio' in df_acc.columns else ()
    df_fotos = load_fotos_cantidades(folios) if folios else pd.DataFrame()

    for _, reg in df_acc.iterrows():
        folio    = str(reg.get('folio', '—'))
        actividad = str(reg.get('tipo_actividad', '—'))
        item      = str(reg.get('item_pago', '—'))
        tramo     = str(reg.get('id_tramo', '—'))
        civ       = str(reg.get('civ', '—'))
        est       = str(reg.get('estado', ''))

        titulo = f"**{folio}** · {actividad} · ítem {item}"

        with st.expander(titulo, expanded=False):
            cd1, cd2 = st.columns([2.5, 1.2])

            with cd1:
                st.markdown(f"""
                <div style="display:flex; gap:6px; align-items:center; margin-bottom:0.7rem; flex-wrap:wrap;">
                    {badge(est)}
                    {tipo_tag('cantidades','Cantidades')}
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:#6e7681;">
                        {str(reg.get('fecha_creacion',''))[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                # Info grid
                i1, i2, i3 = st.columns(3)
                with i1:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield','—')}")
                    st.markdown(f"**Tramo:** {tramo}")
                    st.markdown(f"**CIV:** {civ}")
                with i2:
                    st.markdown(f"**Capítulo:** {reg.get('capitulo','—')}")
                    st.markdown(f"**Ítem:** {item}")
                    st.markdown(f"**Unidad:** {reg.get('unidad','—')}")
                with i3:
                    cant = safe_float(reg.get('cantidad')) or 0
                    cant_res = safe_float(reg.get('cant_residente'))
                    cant_int = safe_float(reg.get('cant_interventor'))
                    st.metric("Cant. Inspector", f"{cant:.3f}")
                    if cant_res is not None:
                        st.metric("Cant. Residente", f"{cant_res:.3f}")
                    if cant_int is not None:
                        st.metric("Cant. Interventor", f"{cant_int:.3f}")

                if reg.get('observaciones'):
                    st.markdown(f'<div class="info-box">📝 {reg["observaciones"]}</div>', unsafe_allow_html=True)

                # Fotos
                if not df_fotos.empty and 'folio' in df_fotos.columns:
                    fotos_reg = df_fotos[df_fotos['folio'] == folio]
                    urls = fotos_reg['foto_url'].dropna().tolist() if not fotos_reg.empty else []
                else:
                    urls = []
                    # Fallback: look for inline foto columns
                    for i in range(1, 6):
                        u = reg.get(f'foto_{i}_url')
                        if u:
                            urls.append(u)

                if urls:
                    st.markdown("**📷 Registro fotográfico**")
                    f_cols = st.columns(min(len(urls), 4))
                    for i, url in enumerate(urls[:4]):
                        with f_cols[i]:
                            st.image(url, use_column_width=True)
                else:
                    st.caption("Sin fotos registradas")

            with cd2:
                render_panel_aprobacion(
                    tabla='registros_cantidades',
                    reg=dict(reg),
                    perfil=perfil,
                    con_cantidad=True
                )


# ══════════════════════════════════════════════════════════════
# 4. MAPA EJECUCIÓN
# ══════════════════════════════════════════════════════════════

def page_mapa_ejecucion(perfil):
    st.markdown("### Mapa de Ejecución de Obra")

    # ── Filtros ──────────────────────────────────────────────
    fm1, fm2, fm3, fm4 = st.columns(4)
    with fm1: fi = st.date_input("Desde", value=date.today()-timedelta(days=30), key="mp_fi")
    with fm2: ff = st.date_input("Hasta", value=date.today(), key="mp_ff")
    with fm3: estado_f = st.selectbox("Estado", ["Todos","BORRADOR","REVISADO","APROBADO","DEVUELTO"], key="mp_est")
    with fm4: civ_f = st.text_input("🔍 CIV", key="mp_civ")

    fm5, fm6, fm7 = st.columns(3)
    with fm5: tramo_f  = st.text_input("🔍 Tramo", key="mp_tramo")
    with fm6: capitulo_f = st.text_input("🔍 Capítulo", key="mp_cap")
    with fm7:
        capas = st.multiselect(
            "Capas visibles",
            ["Cantidades", "Componentes", "Reporte Diario"],
            default=["Cantidades", "Reporte Diario"],
            key="mp_capas"
        )

    estados_q = None if estado_f == "Todos" else [estado_f]
    frames = []

    COLOR_MAP = {
        'BORRADOR': '#a0aec0',
        'REVISADO': '#3fb950',
        'APROBADO': '#388bfd',
        'DEVUELTO': '#f85149',
    }

    # Cargar capas
    if "Cantidades" in capas:
        df_c = load_cantidades(estados=estados_q, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        if not df_c.empty:
            df_c = df_c.dropna(subset=['latitud','longitud'])
            df_c['lat'] = pd.to_numeric(df_c['latitud'],  errors='coerce')
            df_c['lon'] = pd.to_numeric(df_c['longitud'], errors='coerce')
            df_c = df_c.dropna(subset=['lat','lon'])
            df_c['_tipo'] = 'Cantidades'
            df_c['_info'] = df_c.apply(lambda r:
                f"Folio: {r.get('folio','—')}<br>"
                f"Actividad: {r.get('tipo_actividad','—')}<br>"
                f"Ítem: {r.get('item_pago','—')}<br>"
                f"CIV: {r.get('civ','—')}<br>"
                f"Cant: {r.get('cantidad','—')} {r.get('unidad','')}", axis=1)
            frames.append(df_c)

    if "Componentes" in capas:
        df_comp = load_componentes(estados=estados_q, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        if not df_comp.empty:
            df_comp = df_comp.dropna(subset=['latitud','longitud'])
            df_comp['lat'] = pd.to_numeric(df_comp['latitud'],  errors='coerce')
            df_comp['lon'] = pd.to_numeric(df_comp['longitud'], errors='coerce')
            df_comp = df_comp.dropna(subset=['lat','lon'])
            df_comp['_tipo'] = df_comp.get('componente', pd.Series('Componente', index=df_comp.index))
            df_comp['_info'] = df_comp.apply(lambda r:
                f"Folio: {r.get('folio','—')}<br>"
                f"Componente: {r.get('componente','—')}<br>"
                f"Actividad: {r.get('tipo_actividad','—')}<br>"
                f"CIV: {r.get('civ','—')}<br>"
                f"Cant: {r.get('cantidad','—')} {r.get('unidad','')}", axis=1)
            frames.append(df_comp)

    if "Reporte Diario" in capas:
        df_rd = load_reporte_diario(estados=estados_q, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        if not df_rd.empty:
            df_rd = df_rd.dropna(subset=['latitud','longitud'])
            df_rd['lat'] = pd.to_numeric(df_rd['latitud'],  errors='coerce')
            df_rd['lon'] = pd.to_numeric(df_rd['longitud'], errors='coerce')
            df_rd = df_rd.dropna(subset=['lat','lon'])
            df_rd['_tipo'] = 'Reporte Diario'
            df_rd['_info'] = df_rd.apply(lambda r:
                f"Folio: {r.get('folio','—')}<br>"
                f"Fecha: {str(r.get('fecha_reporte',''))[:10]}<br>"
                f"Usuario: {r.get('usuario_qfield','—')}<br>"
                f"Obs: {str(r.get('observaciones',''))[:80]}", axis=1)
            frames.append(df_rd)

    # Filtros de texto
    geo_frames = []
    for df_f in frames:
        if civ_f and 'civ' in df_f.columns:
            df_f = df_f[df_f['civ'].astype(str).str.contains(civ_f, case=False, na=False)]
        if tramo_f:
            t_mask = pd.Series(False, index=df_f.index)
            for col in ['id_tramo','tramo_descripcion','tramo']:
                if col in df_f.columns:
                    t_mask |= df_f[col].astype(str).str.contains(tramo_f, case=False, na=False)
            df_f = df_f[t_mask]
        if capitulo_f and 'capitulo' in df_f.columns:
            df_f = df_f[df_f['capitulo'].astype(str).str.contains(capitulo_f, case=False, na=False)]
        if not df_f.empty:
            geo_frames.append(df_f)

    if not geo_frames:
        st.info("No hay registros con coordenadas GPS para los filtros seleccionados.")
        return

    df_geo = pd.concat(geo_frames, ignore_index=True, sort=False)

    # ── Indicadores del mapa ─────────────────────────────────
    sec_title("Indicadores por Filtros Activos")
    im1, im2, im3, im4 = st.columns(4)
    with im1: kpi("Puntos en mapa", str(len(df_geo)))
    with im2: kpi("Aprobados",  str(len(df_geo[df_geo['estado']=='APROBADO']))  if 'estado' in df_geo else "—", accent="kpi-info")
    with im3: kpi("Revisados",  str(len(df_geo[df_geo['estado']=='REVISADO']))  if 'estado' in df_geo else "—", accent="kpi-accent")
    with im4: kpi("Capas activas", str(len(geo_frames)))

    # ── Mapa ────────────────────────────────────────────────
    tipo_colors = {
        'Cantidades':    '#388bfd',
        'Reporte Diario': '#C8102E',
    }
    # Override: color by estado
    df_geo['_color_state'] = df_geo.get('estado', pd.Series('BORRADOR', index=df_geo.index)).map(COLOR_MAP).fillna('#a0aec0')

    fig = px.scatter_mapbox(
        df_geo,
        lat='lat', lon='lon',
        color='estado' if 'estado' in df_geo.columns else '_tipo',
        color_discrete_map=COLOR_MAP,
        symbol='_tipo',
        hover_name='_info',
        hover_data={
            'folio':  True  if 'folio' in df_geo.columns else False,
            '_tipo':  True,
            'estado': True  if 'estado' in df_geo.columns else False,
            'lat': False, 'lon': False, '_info': False,
        },
        size_max=12,
        zoom=11,
        height=580,
        mapbox_style='carto-darkmatter',
    )
    fig.update_traces(marker_size=10, marker_opacity=0.85)
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            bgcolor='#161b22', bordercolor='#21262d', borderwidth=1,
            font=dict(family='IBM Plex Mono', color='#c9d1d9', size=10),
            title_text='Estado',
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{len(df_geo)} puntos con coordenadas GPS")

    # ── Selección de reporte ─────────────────────────────────
    if 'folio' in df_geo.columns:
        st.divider()
        sec_title("Ver Detalle de Reporte")
        folios_disp = sorted(df_geo['folio'].dropna().unique().tolist())
        sel_folio = st.selectbox("Seleccionar folio para ver detalle", ["—"] + folios_disp, key="mp_sel")
        if sel_folio and sel_folio != "—":
            row = df_geo[df_geo['folio'] == sel_folio].iloc[0]
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Folio</div>
                    <div class="kpi-value">{row.get('folio','—')}</div>
                    <div class="kpi-sub">Tipo: {row.get('_tipo','—')} · Estado: {row.get('estado','—')}</div>
                </div>
                """, unsafe_allow_html=True)
                if row.get('observaciones'):
                    st.markdown(f'<div class="info-box">📝 {row["observaciones"]}</div>', unsafe_allow_html=True)
            with col_d2:
                # Try to load photo
                fotos = load_fotos_cantidades((sel_folio,))
                if fotos.empty:
                    fotos = load_fotos_reporte((sel_folio,))
                if fotos.empty:
                    fotos = load_fotos_componentes((sel_folio,))
                if not fotos.empty:
                    urls = fotos['foto_url'].dropna().tolist()
                    if urls:
                        st.image(urls[0], use_column_width=True, caption=sel_folio)


# ══════════════════════════════════════════════════════════════
# 5. SEGUIMIENTO PRESUPUESTO
# ══════════════════════════════════════════════════════════════

def page_seguimiento_presupuesto(perfil):
    st.markdown("### Seguimiento de Presupuesto")

    df_ppto = load_presupuesto()
    df_comp_ppto = load_presupuesto_componentes()

    if df_ppto.empty:
        st.info("Sin datos en `presupuesto_bd`. Verifica la sincronización del Excel.")
        return

    # Calcular ejecutado desde registros_cantidades aprobados
    df_cant = load_cantidades(estados=['APROBADO'])
    if not df_cant.empty and 'item_pago' in df_cant.columns and 'cant_interventor' in df_cant.columns:
        df_ejec = (
            df_cant
            .groupby('item_pago', dropna=True)['cant_interventor']
            .apply(lambda x: pd.to_numeric(x, errors='coerce').sum())
            .reset_index(name='cant_ejecutada')
        )
        df_ppto = df_ppto.merge(df_ejec, on='item_pago', how='left')
    else:
        df_ppto['cant_ejecutada'] = 0.0

    df_ppto['cant_ejecutada'] = pd.to_numeric(df_ppto.get('cant_ejecutada', 0), errors='coerce').fillna(0)
    df_ppto['cant_ppto']      = pd.to_numeric(df_ppto.get('cantidad_ppto', 0), errors='coerce').fillna(0)
    df_ppto['pct_ejec']       = (df_ppto['cant_ejecutada'] / df_ppto['cant_ppto'].replace(0, float('nan')) * 100).round(2)

    # Merge con precios de presupuesto_componentes_bd si existe
    if not df_comp_ppto.empty and 'item_pago' in df_comp_ppto.columns and 'precio_unitario' in df_comp_ppto.columns:
        precios = df_comp_ppto[['item_pago','precio_unitario']].drop_duplicates('item_pago')
        df_ppto = df_ppto.merge(precios, on='item_pago', how='left')
        df_ppto['precio_unitario'] = pd.to_numeric(df_ppto.get('precio_unitario', 0), errors='coerce').fillna(0)
        df_ppto['valor_ppto']   = df_ppto['cant_ppto']   * df_ppto['precio_unitario']
        df_ppto['valor_ejec']   = df_ppto['cant_ejecutada'] * df_ppto['precio_unitario']
    else:
        df_ppto['precio_unitario'] = 0
        df_ppto['valor_ppto']   = 0
        df_ppto['valor_ejec']   = 0

    # ── Filtros ──────────────────────────────────────────────
    fp1, fp2, fp3 = st.columns(3)
    with fp1:
        caps = ['Todos'] + sorted(df_ppto['capitulo'].dropna().unique().tolist()) if 'capitulo' in df_ppto.columns else ['Todos']
        cap_f = st.selectbox("Capítulo", caps, key="pp_cap")
    with fp2:
        ta_opts = ['Todos'] + sorted(df_ppto['tipo_actividad'].dropna().unique().tolist()) if 'tipo_actividad' in df_ppto.columns else ['Todos']
        ta_f = st.selectbox("Tipo Actividad", ta_opts, key="pp_ta")
    with fp3:
        buscar = st.text_input("🔍 Ítem / Descripción", key="pp_bus")

    df_f = df_ppto.copy()
    if cap_f != 'Todos' and 'capitulo' in df_f.columns:
        df_f = df_f[df_f['capitulo'] == cap_f]
    if ta_f != 'Todos' and 'tipo_actividad' in df_f.columns:
        df_f = df_f[df_f['tipo_actividad'] == ta_f]
    if buscar:
        mask = pd.Series(False, index=df_f.index)
        for col in ['item_pago','descripcion','capitulo','codigo_idu']:
            if col in df_f.columns:
                mask |= df_f[col].astype(str).str.contains(buscar, case=False, na=False)
        df_f = df_f[mask]

    if df_f.empty:
        st.info("Sin resultados para los filtros seleccionados.")
        return

    # ── Indicadores ──────────────────────────────────────────
    sec_title("Indicadores de Ejecución")
    total_items   = len(df_f)
    items_con_eje = len(df_f[df_f['cant_ejecutada'] > 0])
    pct_items     = round(items_con_eje / total_items * 100, 1) if total_items > 0 else 0

    ki1, ki2, ki3, ki4 = st.columns(4)
    with ki1: kpi("Ítems en presupuesto", str(total_items))
    with ki2: kpi("Ítems con ejecución", str(items_con_eje),
                  sub=f"{pct_items}% del total", accent="kpi-accent")
    if df_f['valor_ppto'].sum() > 0:
        with ki3: kpi("Valor Presupuestado", fmt_cop(df_f['valor_ppto'].sum()),
                      card_cls="kpi-card-blue")
        pct_v = round(df_f['valor_ejec'].sum() / df_f['valor_ppto'].sum() * 100, 1) if df_f['valor_ppto'].sum() > 0 else 0
        with ki4: kpi("Valor Ejecutado (aprobado)", fmt_cop(df_f['valor_ejec'].sum()),
                      sub=f"{pct_v}%", accent="kpi-accent", card_cls="kpi-card-green")
    else:
        with ki3: kpi("Ítems sin precio_unitario", "—",
                      sub="Verificar presupuesto_componentes_bd")
        with ki4: kpi("% Ejecución (cant.)",
                      f"{round(df_f['cant_ejecutada'].sum() / df_f['cant_ppto'].sum() * 100, 1) if df_f['cant_ppto'].sum() > 0 else 0}%",
                      accent="kpi-accent")

    st.divider()

    # ── Tabla ────────────────────────────────────────────────
    show_cols = ['capitulo_num','capitulo','tipo_actividad','codigo_idu','item_pago',
                 'descripcion','unidad','cant_ppto','cant_ejecutada','pct_ejec']
    if df_f['valor_ppto'].sum() > 0:
        show_cols += ['precio_unitario','valor_ppto','valor_ejec']
    show_cols = [c for c in show_cols if c in df_f.columns]

    st.dataframe(
        df_f[show_cols],
        hide_index=True,
        use_container_width=True,
        column_config={
            'cant_ppto':        st.column_config.NumberColumn('Cant. Ppto.',    format="%.4f"),
            'cant_ejecutada':   st.column_config.NumberColumn('Cant. Ejecutada',format="%.4f"),
            'pct_ejec':         st.column_config.ProgressColumn('% Ejec.', format="%.1f%%", min_value=0, max_value=100),
            'precio_unitario':  st.column_config.NumberColumn('P.U. ($)', format="$%,.2f"),
            'valor_ppto':       st.column_config.NumberColumn('Valor Ppto. ($)',format="$%,.0f"),
            'valor_ejec':       st.column_config.NumberColumn('Valor Ejec. ($)',format="$%,.0f"),
        }
    )

    # Gráfico por capítulo
    if 'capitulo' in df_f.columns and len(df_f) > 0:
        df_cap = df_f.groupby('capitulo').agg(
            ppto=('cant_ppto','sum'),
            ejec=('cant_ejecutada','sum')
        ).reset_index()
        df_cap['pct'] = (df_cap['ejec'] / df_cap['ppto'].replace(0, float('nan')) * 100).round(1)
        fig = px.bar(df_cap, x='capitulo', y='pct',
                     text='pct', height=280,
                     color='pct',
                     color_continuous_scale=['#C8102E','#d29922','#3fb950'],
                     labels={'pct':'% Ejecución','capitulo':'Capítulo'},
                     range_color=[0, 100])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='IBM Plex Sans', color='#8b949e'),
            coloraxis_showscale=False,
            xaxis=dict(gridcolor='#1c2333'),
            yaxis=dict(gridcolor='#1c2333', ticksuffix='%'),
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # CSV
    csv = df_f[show_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name="Presupuesto_ejecucion.csv",
        mime="text/csv"
    )


# ══════════════════════════════════════════════════════════════
# COMPONENTES TRANSVERSALES — base común
# ══════════════════════════════════════════════════════════════

def panel_componente(perfil, componente_key: str, titulo: str, tipo_label: str):
    """
    componente_key: usado para filtrar registros_componentes.componente
    título y tipo_label para UI.
    """
    rol = perfil['rol']
    st.markdown(f"### {titulo}")

    # ── Filtros ──────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1: fi = st.date_input("Desde", value=date.today()-timedelta(days=30), key=f"{componente_key}_fi")
    with fc2: ff = st.date_input("Hasta", value=date.today(), key=f"{componente_key}_ff")
    with fc3:
        cfg = APR_CFG.get(rol, (None, None, None))
        est_opts = cfg[0] if cfg[0] else ["BORRADOR","REVISADO","APROBADO","DEVUELTO"]
        estado_f = st.selectbox("Estado", ["Todos"] + est_opts, key=f"{componente_key}_est")
    with fc4: buscar = st.text_input("🔍 Folio / Actividad", key=f"{componente_key}_bus")

    estados_q = None if estado_f == "Todos" else [estado_f]
    df = load_componentes(componente=componente_key,
                          estados=estados_q,
                          fecha_ini=fi.isoformat(),
                          fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = pd.Series(False, index=df.index)
        for col in ['folio','item_pago','item_descripcion','tipo_actividad','capitulo','usuario_qfield']:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(buscar, case=False, na=False)
        df = df[mask]

    if df.empty:
        st.info(f"No hay registros de {titulo} para los filtros seleccionados.")
        return

    # ── Indicadores ──────────────────────────────────────────
    sec_title("Indicadores del Período")
    ki1, ki2, ki3, ki4, ki5 = st.columns(5)
    with ki1: kpi("Total Registros", str(len(df)))
    with ki2: kpi("Aprobados",  str(len(df[df['estado']=='APROBADO']))  if 'estado' in df else "0", accent="kpi-info")
    with ki3: kpi("Revisados",  str(len(df[df['estado']=='REVISADO']))  if 'estado' in df else "0", accent="kpi-accent")
    with ki4: kpi("Borradores", str(len(df[df['estado'].isin(['BORRADOR','DEVUELTO'])]))  if 'estado' in df else "0", accent="kpi-warn")
    with ki5:
        cant = df['cantidad'].apply(safe_float).sum() if 'cantidad' in df.columns else 0
        kpi("Cant. Acumulada", f"{cant:,.2f}", accent="kpi-idu")

    # Cantidad aprobada
    if 'cant_interventor' in df.columns:
        cant_apr = df[df['estado']=='APROBADO']['cant_interventor'].apply(safe_float).sum()
        st.markdown(f'<div class="info-box">✅ Cantidad aprobada acumulada: <strong>{cant_apr:,.2f}</strong></div>',
                    unsafe_allow_html=True)

    # Gráfico por capítulo
    if 'capitulo' in df.columns and df['capitulo'].notna().any():
        df_cap = df.groupby('capitulo').agg(
            total=('cantidad', lambda x: pd.to_numeric(x, errors='coerce').sum())
        ).reset_index()
        if len(df_cap) > 1:
            fig = px.pie(df_cap, values='total', names='capitulo',
                         height=200, hole=0.55,
                         color_discrete_sequence=['#C8102E','#388bfd','#3fb950','#d29922','#f85149'])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='IBM Plex Sans', color='#8b949e', size=11),
                margin=dict(l=0,r=0,t=10,b=0),
                showlegend=True,
                legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

    st.divider()

    # ── Tabla resumen ────────────────────────────────────────
    sec_title(f"Registros ({len(df)})")
    show_cols = ['folio','usuario_qfield','civ','id_tramo','tipo_actividad','capitulo',
                 'item_pago','item_descripcion','unidad','cantidad','cant_residente',
                 'cant_interventor','estado','fecha_reporte']
    show_cols = [c for c in show_cols if c in df.columns]
    st.dataframe(
        df[show_cols],
        hide_index=True,
        use_container_width=True,
        column_config={
            'cantidad':         st.column_config.NumberColumn('Cant. Inspector', format="%.3f"),
            'cant_residente':   st.column_config.NumberColumn('Cant. Residente', format="%.3f"),
            'cant_interventor': st.column_config.NumberColumn('Cant. Interventor', format="%.3f"),
            'fecha_reporte':    st.column_config.DateColumn('Fecha reporte', format="DD/MM/YYYY"),
        }
    )

    # CSV
    csv = df[show_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Exportar CSV",
        data=csv,
        file_name=f"Componente_{componente_key}_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    st.divider()

    # ── Detalle con aprobación ──────────────────────────────
    sec_title("Detalle y Aprobación")

    cfg = APR_CFG.get(rol, (None, None, None))
    est_vis = cfg[0]
    if est_vis:
        df_acc = df[df['estado'].isin(est_vis)] if 'estado' in df.columns else df
    else:
        df_acc = df

    if df_acc.empty:
        st.markdown('<div class="info-box">✅ Sin registros pendientes para tu rol.</div>', unsafe_allow_html=True)
        df_acc = df

    folios = tuple(df_acc['folio'].dropna().unique().tolist()) if 'folio' in df_acc.columns else ()
    df_fotos = load_fotos_componentes(folios) if folios else pd.DataFrame()

    for _, reg in df_acc.iterrows():
        folio     = str(reg.get('folio', '—'))
        actividad = str(reg.get('tipo_actividad', '—'))
        item      = str(reg.get('item_pago', '—'))
        est       = str(reg.get('estado', ''))

        with st.expander(f"**{folio}** · {actividad} · {item}", expanded=False):
            cd1, cd2 = st.columns([2.5, 1.2])

            with cd1:
                st.markdown(f"""
                <div style="display:flex; gap:6px; align-items:center; margin-bottom:0.7rem; flex-wrap:wrap;">
                    {badge(est)}
                    {tipo_tag(componente_key.lower(), tipo_label)}
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:#6e7681;">
                        {str(reg.get('fecha_reporte', reg.get('fecha_creacion','')))[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                i1, i2, i3 = st.columns(3)
                with i1:
                    st.markdown(f"**Profesional:** {reg.get('profesional', reg.get('usuario_qfield','—'))}")
                    st.markdown(f"**CIV:** {reg.get('civ','—')}")
                    st.markdown(f"**Tramo:** {reg.get('id_tramo', reg.get('tramo','—'))}")
                with i2:
                    st.markdown(f"**Capítulo:** {reg.get('capitulo','—')}")
                    st.markdown(f"**Ítem:** {item}")
                    st.markdown(f"**Unidad:** {reg.get('unidad','—')}")
                with i3:
                    cant = safe_float(reg.get('cantidad')) or 0
                    cant_res = safe_float(reg.get('cant_residente'))
                    cant_int = safe_float(reg.get('cant_interventor'))
                    st.metric("Cant. Inspector", f"{cant:.3f}")
                    if cant_res is not None:
                        st.metric("Cant. Residente", f"{cant_res:.3f}")
                    if cant_int is not None:
                        st.metric("Cant. Interventor", f"{cant_int:.3f}")

                if reg.get('observaciones'):
                    st.markdown(f'<div class="info-box">📝 {reg["observaciones"]}</div>', unsafe_allow_html=True)

                # Fotos
                if not df_fotos.empty and 'folio' in df_fotos.columns:
                    fotos_reg = df_fotos[df_fotos['folio'] == folio]
                    urls = fotos_reg['foto_url'].dropna().tolist() if not fotos_reg.empty else []
                    if urls:
                        st.markdown("**📷 Registro fotográfico**")
                        f_cols = st.columns(min(len(urls), 4))
                        for i, url in enumerate(urls[:4]):
                            with f_cols[i]:
                                st.image(url, use_column_width=True)

            with cd2:
                render_panel_aprobacion(
                    tabla='registros_componentes',
                    reg=dict(reg),
                    perfil=perfil,
                    con_cantidad=True
                )


def page_social(perfil):
    panel_componente(perfil, "Social", "Componente Social", "Social")


def page_ambiental(perfil):
    panel_componente(perfil, "Ambiental", "Componente Ambiental · SST", "Ambiental-SST")


def page_pmt(perfil):
    st.markdown("### Componente PMT")

    # Mostrar formulario_pmt primero
    sec_title("PMTs Registrados (Formulario PMT)")
    try:
        sb = get_supabase()
        r  = sb.table('formulario_pmt').select('*').eq('contrato_id','IDU-1556-2025').execute()
        df_pmt = pd.DataFrame(r.data) if r.data else pd.DataFrame()
    except Exception:
        df_pmt = pd.DataFrame()

    if df_pmt.empty:
        st.markdown('<div class="info-box">Sin PMTs en formulario_pmt. Verifica sincronización QField.</div>', unsafe_allow_html=True)
    else:
        pmt_cols = ['folio','civ','descripcion','inicio_vigencia','fin_vigencia','usuario','latitud','longitud']
        pmt_cols = [c for c in pmt_cols if c in df_pmt.columns]
        st.dataframe(
            df_pmt[pmt_cols],
            hide_index=True,
            use_container_width=True,
            column_config={
                'inicio_vigencia': st.column_config.DateColumn('Inicio vigencia', format="DD/MM/YYYY"),
                'fin_vigencia':    st.column_config.DateColumn('Fin vigencia',    format="DD/MM/YYYY"),
            }
        )

        # Alertas vencimiento
        if 'fin_vigencia' in df_pmt.columns:
            df_pmt['fin_vigencia_d'] = pd.to_datetime(df_pmt['fin_vigencia'], errors='coerce').dt.date
            vencidos = df_pmt[df_pmt['fin_vigencia_d'] < date.today()]
            proximos = df_pmt[(df_pmt['fin_vigencia_d'] >= date.today()) &
                              (df_pmt['fin_vigencia_d'] <= date.today() + timedelta(days=15))]
            if not vencidos.empty:
                st.markdown(f'<div class="warn-box">⚠️ {len(vencidos)} PMT(s) VENCIDO(S) — requieren renovación</div>',
                            unsafe_allow_html=True)
            if not proximos.empty:
                st.markdown(f'<div class="info-box">📅 {len(proximos)} PMT(s) vencen en los próximos 15 días</div>',
                            unsafe_allow_html=True)

    st.divider()
    # Cantidades ejecutadas PMT
    panel_componente(perfil, "PMT", "Ejecución Cantidades — PMT", "PMT")


# ══════════════════════════════════════════════════════════════
# 9. GENERAR INFORME
# ══════════════════════════════════════════════════════════════

def page_generar_informe(perfil):
    st.markdown("### Generar Informe — Bitácora de Obra")

    # ── Configuración del informe ─────────────────────────────
    gi1, gi2 = st.columns(2)
    with gi1:
        fi = st.date_input("Fecha inicio del período", value=date.today()-timedelta(days=7), key="gi_fi")
        ff = st.date_input("Fecha fin del período",    value=date.today(),                   key="gi_ff")
    with gi2:
        incluir = st.multiselect(
            "Tipos de registro a incluir",
            ["Cantidades", "Reporte Diario", "Componente Social",
             "Componente Ambiental-SST", "Componente PMT"],
            default=["Cantidades", "Reporte Diario"],
            key="gi_inc"
        )
        estados_inc = st.multiselect(
            "Estados a incluir",
            ["BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"],
            default=["REVISADO", "APROBADO"],
            key="gi_est"
        )

    if not incluir:
        st.warning("Selecciona al menos un tipo de registro.")
        return

    st.divider()
    sec_title("Vista Previa del Informe")

    frames_inf = {}
    total_registros = 0

    if "Cantidades" in incluir:
        df_c = load_cantidades(estados=estados_inc or None,
                               fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        if not df_c.empty:
            frames_inf["Cantidades"] = df_c
            total_registros += len(df_c)

    if "Reporte Diario" in incluir:
        df_rd = load_reporte_diario(estados=estados_inc or None,
                                    fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        if not df_rd.empty:
            frames_inf["Reporte Diario"] = df_rd
            total_registros += len(df_rd)

    comp_map = {
        "Componente Social": "Social",
        "Componente Ambiental-SST": "Ambiental",
        "Componente PMT": "PMT",
    }
    for key, comp_key in comp_map.items():
        if key in incluir:
            df_comp = load_componentes(componente=comp_key, estados=estados_inc or None,
                                       fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
            if not df_comp.empty:
                frames_inf[key] = df_comp
                total_registros += len(df_comp)

    # Indicadores resumen
    ki1, ki2, ki3 = st.columns(3)
    with ki1: kpi("Total Registros", str(total_registros))
    with ki2: kpi("Período",
                  f"{fi.strftime('%d/%m/%Y')} – {ff.strftime('%d/%m/%Y')}")
    with ki3: kpi("Tipos incluidos", str(len(frames_inf)))

    if not frames_inf:
        st.info("No hay registros para los filtros seleccionados.")
        return

    # Previsualización por tipo
    for tipo_inf, df_inf in frames_inf.items():
        st.markdown(f"**{tipo_inf}** — {len(df_inf)} registro(s)")
        preview_cols = [c for c in ['folio','usuario_qfield','estado','fecha_creacion',
                                    'tipo_actividad','item_pago','cantidad','cant_interventor',
                                    'observaciones']
                        if c in df_inf.columns]
        st.dataframe(
            df_inf[preview_cols].head(10),
            hide_index=True,
            use_container_width=True,
            column_config={
                'cant_interventor': st.column_config.NumberColumn('Cant. Aprobada', format="%.3f"),
                'fecha_creacion': st.column_config.DatetimeColumn('Fecha', format="DD/MM/YY HH:mm"),
            }
        )
        if len(df_inf) > 10:
            st.caption(f"... y {len(df_inf)-10} registros más en la exportación")

    # ── Exportar ─────────────────────────────────────────────
    st.divider()
    sec_title("Exportar Informe")

    # Multi-sheet Excel en memoria
    col_exp1, col_exp2 = st.columns(2)

    with col_exp1:
        # CSV combinado
        dfs_concat = []
        for tipo_inf, df_inf in frames_inf.items():
            df_inf_cp = df_inf.copy()
            df_inf_cp['_tipo'] = tipo_inf
            dfs_concat.append(df_inf_cp)
        if dfs_concat:
            df_all = pd.concat(dfs_concat, ignore_index=True, sort=False)
            csv_all = df_all.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Descargar CSV (todos los tipos)",
                data=csv_all,
                file_name=f"Bitacora_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_exp2:
        # Excel multi-hoja
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                for tipo_inf, df_inf in frames_inf.items():
                    sheet_name = tipo_inf[:31]  # Excel limit
                    df_inf.to_excel(writer, sheet_name=sheet_name, index=False)
            output.seek(0)
            st.download_button(
                "📊 Descargar Excel (multi-hoja)",
                data=output,
                file_name=f"Bitacora_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except ImportError:
            st.caption("openpyxl no disponible — usa el CSV")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

PAGE_MAP = {
    "Estado Actual":            page_estado_actual,
    "Anotaciones Diario":       page_anotaciones_diario,
    "Reporte Cantidades":       page_reporte_cantidades,
    "Mapa Ejecución":           page_mapa_ejecucion,
    "Seguimiento Presupuesto":  page_seguimiento_presupuesto,
    "Componente Social":        page_social,
    "Componente Ambiental-SST": page_ambiental,
    "Componente PMT":           page_pmt,
    "Generar Informe":          page_generar_informe,
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
            st.error(f"Error al cargar la página '{page}': {e}")
            import traceback
            st.code(traceback.format_exc())
    else:
        st.error(f"Página '{page}' no encontrada.")


if __name__ == '__main__':
    main()
