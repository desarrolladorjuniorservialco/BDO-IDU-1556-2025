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
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Fondo app ── */
.stApp { background: #0d1117; color: #c9d1d9; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0a0e16;
    border-right: 1px solid #1c2333;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label {
    color: #8b949e !important;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    text-transform: none !important;
    font-size: 0.88rem;
    letter-spacing: 0;
    color: #c9d1d9 !important;
}

/* ── Categorías sidebar ── */
.nav-category {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #388bfd !important;
    padding: 0.6rem 0 0.2rem 0;
    border-top: 1px solid #1c2333;
    margin-top: 0.4rem;
}
.nav-category:first-child { border-top: none; margin-top: 0; }

/* ── Métricas / KPI cards ── */
.kpi-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    margin-bottom: 0.5rem;
}
.kpi-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b949e;
    margin-bottom: 0.25rem;
    font-family: 'IBM Plex Mono', monospace;
}
.kpi-value {
    font-size: 1.55rem;
    font-weight: 600;
    color: #e6edf3;
    line-height: 1.2;
}
.kpi-sub {
    font-size: 0.75rem;
    color: #6e7681;
    margin-top: 0.15rem;
}
.kpi-accent { color: #3fb950; }
.kpi-warn   { color: #d29922; }
.kpi-danger { color: #f85149; }
.kpi-info   { color: #388bfd; }

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
hr { border-color: #21262d; }

/* ── Expanders ── */
details summary {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
}

/* ── Headings ── */
h1,h2,h3 { font-family: 'IBM Plex Sans', sans-serif; font-weight: 600; color: #e6edf3; }
h3 { border-bottom: 1px solid #21262d; padding-bottom: 0.4rem; margin-bottom: 1rem; }

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
.badge-borrador  { background:#21262d; color:#8b949e; }
.badge-revisado  { background:#1f3d2b; color:#3fb950; }
.badge-aprobado  { background:#1a3255; color:#388bfd; }
.badge-devuelto  { background:#3d1e1e; color:#f85149; }

/* ── Login ── */
.login-box {
    background: #161b22;
    border: 1px solid #21262d;
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
def load_registros(estados=None, fecha_ini=None, fecha_fin=None):
    sb    = get_supabase()
    query = sb.table('registros').select('*')
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
    r  = sb.table('presupuesto').select('*').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_curva_s():
    sb = get_supabase()
    r  = sb.table('curva_s').select('*').order('semana').execute()
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
                    letter-spacing:0.14em; color:#388bfd; text-transform:uppercase;
                    margin-bottom:0.25rem;">
            Sistema de Bitácora Digital
        </div>
        <div style="font-size:1.8rem; font-weight:600; color:#e6edf3; margin-bottom:0.1rem;">
            BDO · IDU-1556-2025
        </div>
        <div style="font-size:0.85rem; color:#6e7681; margin-bottom:2rem;">
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
# SIDEBAR
# ══════════════════════════════════════════════════════════════

# Mapa de acceso por rol
NAV_ACCESS = {
    # Bitácora
    "Estado Actual":              ['inspector','residente','residente_amb','residente_social','interventor','int_amb','int_social','supervisor','admin'],
    "Anotaciones":                ['inspector','residente','residente_amb','residente_social','interventor','int_amb','int_social','supervisor','admin'],
    "Generar PDF":                ['residente','interventor','supervisor','admin'],
    # Seguimiento
    "Reporte Cantidades":         ['residente','interventor','supervisor','admin'],
    "Mapa de Obra":               ['residente','interventor','supervisor','admin'],
    "Seguimiento Presupuesto":    ['residente','interventor','supervisor','admin'],
    "Curva S":                    ['residente','interventor','supervisor','admin'],
    # Transversales
    "Componente Ambiental - SST": ['residente_amb','int_amb','supervisor','admin'],
    "Componente Social":          ['residente_social','int_social','supervisor','admin'],
    "Componente PMT":             ['residente','interventor','supervisor','admin'],
}

ROL_LABELS = {
    'inspector':       '📋 Inspector',
    'residente':       '✏️ Residente de Obra',
    'residente_amb':   '🌿 Residente Ambiental/SST',
    'residente_social':'🤝 Residente Social',
    'interventor':     '✅ Interventor',
    'int_amb':         '🌿 Interventor Ambiental',
    'int_social':      '🤝 Interventor Social',
    'supervisor':      '👁️ Supervisor IDU',
    'admin':           '⚙️ Administrador',
}


def sidebar(perfil):
    rol = perfil['rol']

    with st.sidebar:
        # Header usuario
        st.markdown(f"""
        <div style="padding:1rem 0 0.5rem 0; border-bottom:1px solid #1c2333; margin-bottom:0.5rem;">
            <div style="font-size:0.72rem; color:#6e7681; font-family:'IBM Plex Mono',monospace;
                        text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.2rem;">
                {ROL_LABELS.get(rol, rol)}
            </div>
            <div style="font-size:1rem; font-weight:600; color:#e6edf3;">{perfil['nombre']}</div>
            <div style="font-size:0.78rem; color:#8b949e;">{perfil.get('empresa','')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Resumen rápido
        df_q = load_registros()
        if not df_q.empty:
            total = len(df_q)
            apr   = len(df_q[df_q['estado']=='APROBADO'])
            st.markdown(f"""
            <div style="display:flex; gap:0.5rem; margin-bottom:0.75rem; flex-wrap:wrap;">
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
                             background:#161b22;border:1px solid #21262d;border-radius:4px;
                             padding:2px 7px;color:#8b949e;">Total {total}</span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
                             background:#1a3255;border-radius:4px;padding:2px 7px;color:#388bfd;">
                    ✅ {apr}</span>
                <span style="font-family:'IBM Plex Mono',monospace;font-size:0.7rem;
                             background:#3d1e1e;border-radius:4px;padding:2px 7px;color:#f85149;">
                    ↩️ {len(df_q[df_q['estado']=='DEVUELTO'])}</span>
            </div>
            """, unsafe_allow_html=True)

        # ── Navegación por categorías ──────────────────────────
        categories = {
            "Bitácora de Obra": ["Estado Actual", "Anotaciones", "Generar PDF"],
            "Seguimiento de Obra": ["Reporte Cantidades", "Mapa de Obra",
                                    "Seguimiento Presupuesto", "Curva S"],
            "Componentes Transversales": ["Componente Ambiental - SST",
                                          "Componente Social", "Componente PMT"],
        }

        opciones_disponibles = []
        nav_items = []

        for cat, pages in categories.items():
            accesibles = [p for p in pages if rol in NAV_ACCESS.get(p, [])]
            if not accesibles:
                continue
            nav_items.append(("__cat__", cat))
            for page in accesibles:
                nav_items.append(("__page__", page))
                opciones_disponibles.append(page)

        # Render categorías como markdown + radio separados por secciones
        # Usamos un único radio pero agrupamos visualmente
        selected_page = st.session_state.get('current_page', opciones_disponibles[0] if opciones_disponibles else "Estado Actual")

        for item_type, item_val in nav_items:
            if item_type == "__cat__":
                st.markdown(f'<div class="nav-category">{item_val}</div>', unsafe_allow_html=True)
            else:
                icon = {
                    "Estado Actual": "◈",
                    "Anotaciones": "◉",
                    "Generar PDF": "◫",
                    "Reporte Cantidades": "◈",
                    "Mapa de Obra": "◉",
                    "Seguimiento Presupuesto": "◈",
                    "Curva S": "◉",
                    "Componente Ambiental - SST": "◈",
                    "Componente Social": "◉",
                    "Componente PMT": "◫",
                }.get(item_val, "◈")

                is_active = selected_page == item_val
                bg = "background:#1c2333;border-radius:5px;" if is_active else ""
                color = "#e6edf3" if is_active else "#8b949e"

                if st.button(
                    f"{icon}  {item_val}",
                    key=f"nav_{item_val}",
                    use_container_width=True,
                ):
                    st.session_state['current_page'] = item_val
                    st.rerun()

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            logout()

    return st.session_state.get('current_page',
                                 opciones_disponibles[0] if opciones_disponibles else "Estado Actual")


# ══════════════════════════════════════════════════════════════
# BITÁCORA 1 — ESTADO ACTUAL
# ══════════════════════════════════════════════════════════════

def page_estado_actual():
    st.markdown("### Estado Actual del Contrato")

    contrato = load_contrato()

    if not contrato:
        st.info("Sin datos de contrato configurados. Verifica la tabla `contratos` en Supabase.")
        # Datos demo para visualización
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

    # Cálculos
    fecha_inicio = datetime.strptime(contrato.get('fecha_inicio','2025-01-01'), '%Y-%m-%d').date()
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

    # ── Fila 1: Info general ──────────────────────────────────
    st.markdown("#### Información General")
    c1, c2, c3 = st.columns(3)

    with c1:
        kpi("Número de Contrato", contrato.get('numero','—'))
        kpi("Entidad Contratante", contrato.get('entidad','—'))

    with c2:
        kpi("Contratista", contrato.get('contratista','—'))
        kpi("Fecha de Inicio", fecha_inicio.strftime('%d/%m/%Y'))

    with c3:
        kpi("Plazo Total", f"{plazo} días", sub=f"+{contrato.get('adicion_plazo_dias',0) or 0} días de adición")
        kpi("Grupos / Localidades",
            "Mártires · S.Cristóbal · R.Uribe<br>Santafé · A.Nariño", accent_class="kpi-info")

    st.markdown(f"""
    <div class="kpi-card" style="margin-bottom:1rem;">
        <div class="kpi-label">Objeto del Contrato</div>
        <div style="color:#c9d1d9; font-size:0.95rem; line-height:1.5;">
            {contrato.get('objeto','—')}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Fila 2: Tiempo ──────────────────────────────────────
    st.markdown("#### Ejecución del Plazo")
    ct1, ct2, ct3, ct4 = st.columns(4)

    accent_tiempo = "kpi-warn" if pct_tiempo > 70 else "kpi-accent"
    with ct1: kpi("Días Transcurridos", str(dias_trans), sub=f"{pct_tiempo}% del plazo", accent_class=accent_tiempo)
    with ct2: kpi("Días Restantes", str(dias_rest))
    with ct3: kpi("Plazo Original", f"{contrato.get('plazo_dias','—')} días")
    with ct4: kpi("Adiciones de Plazo", f"{contrato.get('adicion_plazo_dias',0) or 0} días",
                  accent_class="kpi-warn" if (contrato.get('adicion_plazo_dias') or 0) > 0 else "")

    fig_tiempo = go.Figure(go.Bar(
        x=[pct_tiempo, 100 - pct_tiempo],
        y=["Plazo"],
        orientation='h',
        marker_color=['#388bfd', '#21262d'],
        text=[f"{pct_tiempo}% transcurrido", f"{100-pct_tiempo}% restante"],
        textposition='inside',
        textfont=dict(family="IBM Plex Mono", size=12, color="white"),
    ))
    fig_tiempo.update_layout(
        height=70, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, barmode='stack',
        xaxis=dict(showticklabels=False, range=[0,100]),
        yaxis=dict(showticklabels=False),
    )
    st.plotly_chart(fig_tiempo, use_container_width=True, config={'displayModeBar':False})

    st.divider()

    # ── Fila 3: Financiero ──────────────────────────────────
    st.markdown("#### Ejecución Financiera")
    cf1, cf2, cf3, cf4 = st.columns(4)

    pct_ejec_accent = "kpi-danger" if pct_ejec < pct_tiempo - 15 else ("kpi-accent" if pct_ejec >= 80 else "kpi-warn")
    with cf1: kpi("Valor Contrato", f"${val_act:,.0f}", sub="Actualizado con adiciones", accent_class="kpi-info")
    with cf2: kpi("Valor Ejecutado", f"${val_ejec:,.0f}", sub=f"{pct_ejec}% del contrato", accent_class=pct_ejec_accent)
    with cf3: kpi("Anticipos Desembolsados", f"${val_ant:,.0f}",
                  sub=f"{contrato.get('anticipos_total',0)} anticipo(s)")
    with cf4: kpi("Amortizado", f"${val_amort:,.0f}", sub=f"{pct_amort}% del anticipo",
                  accent_class="kpi-accent" if pct_amort > 50 else "kpi-warn")

    if contrato.get('adicion_valor') and contrato['adicion_valor'] > 0:
        st.markdown(f"""
        <div class="kpi-card" style="border-color:#d29922; margin-top:0.5rem;">
            <div class="kpi-label kpi-warn">Adición de Valor</div>
            <div class="kpi-value kpi-warn">${contrato['adicion_valor']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    # Gauge ejecutado vs tiempo
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_fin = go.Figure()
        fig_fin.add_trace(go.Bar(
            name='Ejecutado', x=['Financiero'], y=[pct_ejec],
            marker_color='#3fb950', text=[f"{pct_ejec}%"], textposition='inside',
            textfont=dict(family="IBM Plex Mono", size=13, color="white"),
        ))
        fig_fin.add_trace(go.Bar(
            name='Pendiente', x=['Financiero'], y=[100-pct_ejec],
            marker_color='#21262d',
        ))
        fig_fin.add_trace(go.Bar(
            name='% Tiempo', x=['Tiempo'], y=[pct_tiempo],
            marker_color='#388bfd', text=[f"{pct_tiempo}%"], textposition='inside',
            textfont=dict(family="IBM Plex Mono", size=13, color="white"),
        ))
        fig_fin.add_trace(go.Bar(
            name='Tiempo rest.', x=['Tiempo'], y=[100-pct_tiempo],
            marker_color='#21262d',
        ))
        fig_fin.update_layout(
            barmode='stack', height=220,
            margin=dict(l=0,r=0,t=20,b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            yaxis=dict(range=[0,100], ticksuffix='%', gridcolor='#1c2333', color='#6e7681'),
            xaxis=dict(color='#8b949e'),
            font=dict(family='IBM Plex Sans', color='#8b949e'),
            title=dict(text='Ejecución Financiera vs Tiempo (%)', font=dict(color='#8b949e', size=12)),
        )
        st.plotly_chart(fig_fin, use_container_width=True, config={'displayModeBar':False})

    with col_g2:
        fig_ant = go.Figure(go.Pie(
            values=[val_amort, val_ant - val_amort],
            labels=['Amortizado','Pendiente'],
            hole=0.65,
            marker_colors=['#388bfd','#21262d'],
            textinfo='none',
        ))
        fig_ant.add_annotation(
            text=f"{pct_amort}%<br><span style='font-size:10px'>amortizado</span>",
            x=0.5, y=0.5, font_size=18, font_color='#e6edf3',
            showarrow=False, font=dict(family='IBM Plex Mono'),
        )
        fig_ant.update_layout(
            height=220, margin=dict(l=0,r=0,t=20,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            title=dict(text='Amortización de Anticipos', font=dict(color='#8b949e', size=12)),
        )
        st.plotly_chart(fig_ant, use_container_width=True, config={'displayModeBar':False})


# ══════════════════════════════════════════════════════════════
# BITÁCORA 2 — ANOTACIONES
# ══════════════════════════════════════════════════════════════

# Lógica de roles para aprobaciones
APROBACION_CONFIG = {
    # rol → (estados que puede ver pendientes, accion aprobar, estado resultado)
    'inspector':        (['BORRADOR'],           None,       None),
    'residente':        (['BORRADOR','DEVUELTO'], 'REVISADO', {
        'campo_cant':  'cant_residente',
        'campo_estado':'estado_residente',
        'campo_apr':   'aprobado_residente',
        'campo_fecha': 'fecha_residente',
        'campo_obs':   'obs_residente',
    }),
    'interventor':      (['REVISADO'],           'APROBADO', {
        'campo_cant':  'cant_interventor',
        'campo_estado':'estado_interventor',
        'campo_apr':   'aprobado_interventor',
        'campo_fecha': 'fecha_interventor',
        'campo_obs':   'obs_interventor',
    }),
    'residente_amb':    (['BORRADOR','DEVUELTO'], 'REVISADO', {
        'campo_cant':  'cant_residente',
        'campo_estado':'estado_residente',
        'campo_apr':   'aprobado_residente',
        'campo_fecha': 'fecha_residente',
        'campo_obs':   'obs_residente',
    }),
    'int_amb':          (['REVISADO'],           'APROBADO', {
        'campo_cant':  'cant_interventor',
        'campo_estado':'estado_interventor',
        'campo_apr':   'aprobado_interventor',
        'campo_fecha': 'fecha_interventor',
        'campo_obs':   'obs_interventor',
    }),
    'residente_social': (['BORRADOR','DEVUELTO'], 'REVISADO', {
        'campo_cant':  'cant_residente',
        'campo_estado':'estado_residente',
        'campo_apr':   'aprobado_residente',
        'campo_fecha': 'fecha_residente',
        'campo_obs':   'obs_residente',
    }),
    'int_social':       (['REVISADO'],           'APROBADO', {
        'campo_cant':  'cant_interventor',
        'campo_estado':'estado_interventor',
        'campo_apr':   'aprobado_interventor',
        'campo_fecha': 'fecha_interventor',
        'campo_obs':   'obs_interventor',
    }),
    'supervisor':       (None,                   None,       None),
    'admin':            (['REVISADO'],           'APROBADO', {
        'campo_cant':  'cant_interventor',
        'campo_estado':'estado_interventor',
        'campo_apr':   'aprobado_interventor',
        'campo_fecha': 'fecha_interventor',
        'campo_obs':   'obs_interventor',
    }),
}


def page_anotaciones(perfil):
    rol = perfil['rol']
    st.markdown("### Anotaciones de Bitácora")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    # Filtros
    c1, c2, c3, c4 = st.columns(4)
    with c1: fi = st.date_input("Desde", value=date.today()-timedelta(days=15))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3:
        if estados_vis:
            estado_f = st.selectbox("Estado", ["Todos"] + estados_vis)
        else:
            estado_f = st.selectbox("Estado", ["Todos","BORRADOR","REVISADO","APROBADO","DEVUELTO"])
    with c4: buscar = st.text_input("🔍 Folio / Actividad / CIV")

    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis  # supervisores/admins ven todo

    df = load_registros(estados=estados_q,
                        fecha_ini=fi.isoformat(),
                        fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = (
            df.get('folio','').astype(str).str.contains(buscar, case=False, na=False) |
            df.get('tipo_actividad','').astype(str).str.contains(buscar, case=False, na=False) |
            df.get('civ','').astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.success("✅ No hay registros para los filtros seleccionados")
        return

    # Contadores
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total", len(df))
    with m2: st.metric("Borradores", len(df[df['estado']=='BORRADOR']) if 'estado' in df else 0)
    with m3: st.metric("Revisados",  len(df[df['estado']=='REVISADO'])  if 'estado' in df else 0)
    with m4: st.metric("Aprobados",  len(df[df['estado']=='APROBADO'])  if 'estado' in df else 0)

    st.divider()

    # Vista solo lectura (supervisor / inspector)
    if not campos:
        cols = ['folio','usuario_qfield','id_tramo','civ','tipo_actividad',
                'cantidad','unidad','estado','fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    # Vista con acciones de aprobación
    st.markdown(f"**{len(df)} registro(s) pendiente(s) de revisión**")

    for _, reg in df.iterrows():
        estado_actual = reg.get('estado', '')
        folio         = reg.get('folio', '—')
        actividad     = reg.get('tipo_actividad', '—')
        tramo         = reg.get('tramo_descripcion', reg.get('id_tramo', '—'))

        titulo = f"**{folio}** · {actividad} · {tramo}"

        with st.expander(titulo, expanded=False):
            ci, ca = st.columns([2.2, 1])

            with ci:
                st.markdown(f"""
                <div style="display:flex; gap:0.5rem; margin-bottom:0.75rem; flex-wrap:wrap;">
                    {badge(estado_actual)}
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:#6e7681;">
                        {str(reg.get('fecha_inicio',''))[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield','—')}")
                    st.markdown(f"**Tramo:** {reg.get('id_tramo','—')}")
                    st.markdown(f"**CIV:** {reg.get('civ','—')}")
                with col_b:
                    st.markdown(f"**Ítem pago:** {reg.get('item_pago','—')}")
                    st.markdown(f"**Cód. elemento:** {reg.get('codigo_elemento','—')}")
                    st.markdown(f"**Unidad:** {reg.get('unidad','—')}")
                with col_c:
                    cant = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cant. inspector", f"{cant:.2f} {reg.get('unidad','')}")
                    if reg.get('cant_residente'):
                        st.metric("Cant. residente", f"{safe_float(reg.get('cant_residente') or 0):.2f}")

                if reg.get('descripcion'):
                    st.info(f"📝 {reg['descripcion']}")

                if reg.get('obs_residente') and rol in ('interventor','int_amb','int_social','admin'):
                    st.warning(f"Obs. residente: {reg['obs_residente']}")

                # Registro fotográfico
                fotos = [reg.get(f'foto_{i}_url') for i in range(1,6) if reg.get(f'foto_{i}_url')]
                if fotos:
                    st.markdown("**📷 Registro fotográfico**")
                    fcols = st.columns(min(len(fotos), 3))
                    for i, url in enumerate(fotos[:3]):
                        with fcols[i]:
                            st.image(url, use_column_width=True)

            # ── Panel de aprobación ──────────────────────────
            with ca:
                st.markdown("**Validación**")
                campo_cant = campos['campo_cant']
                campo_obs  = campos['campo_obs']

                cant_def = safe_float(reg.get(campo_cant)) or safe_float(reg.get('cantidad')) or 0.0

                cant_val = st.number_input(
                    "Cantidad validada",
                    value=float(cant_def),
                    step=0.01,
                    key=f"cant_{reg['id']}"
                )
                obs_val = st.text_area(
                    "Observación",
                    key=f"obs_{reg['id']}",
                    height=80,
                    placeholder="Opcional para aprobar · Obligatoria para devolver"
                )

                b1, b2 = st.columns(2)

                with b1:
                    if st.button("✅ Aprobar", key=f"apr_{reg['id']}",
                                 use_container_width=True, type="primary"):
                        try:
                            sb = get_supabase()
                            update_data = {
                                'estado':            estado_apr,
                                campo_cant:          cant_val,
                                campos['campo_estado']:'aprobado',
                                campos['campo_apr']:  perfil['id'],
                                campos['campo_fecha']: datetime.now().isoformat(),
                            }
                            if obs_val:
                                update_data[campo_obs] = obs_val
                            sb.table('registros').update(update_data).eq('id', reg['id']).execute()
                            clear_cache()
                            st.success("✅ Aprobado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al aprobar: {e}")

                with b2:
                    if st.button("↩️ Devolver", key=f"dev_{reg['id']}",
                                 use_container_width=True):
                        if not obs_val:
                            st.error("Escribe una observación para devolver")
                        else:
                            try:
                                sb = get_supabase()
                                sb.table('registros').update({
                                    'estado':               'DEVUELTO',
                                    campos['campo_estado']:  'devuelto',
                                    campo_obs:              obs_val,
                                    campos['campo_fecha']:  datetime.now().isoformat(),
                                }).eq('id', reg['id']).execute()
                                clear_cache()
                                st.warning("↩️ Devuelto al inspector")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al devolver: {e}")


# ══════════════════════════════════════════════════════════════
# BITÁCORA 3 — GENERAR PDF
# ══════════════════════════════════════════════════════════════

def page_generar_pdf(perfil):
    st.markdown("### Generar PDF de Bitácora")
    st.info("⚠️ Módulo en desarrollo. La generación de PDF se implementará con Jinja2 + WeasyPrint.")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today()-timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    tipo_reporte = st.selectbox(
        "Tipo de reporte",
        ["Bitácora semanal completa", "Solo actividades aprobadas", "Solo anotaciones"]
    )

    incluir = st.multiselect(
        "Incluir secciones",
        ["Registro de actividades", "Registro fotográfico", "Anotaciones", "Cantidades por ítem"],
        default=["Registro de actividades", "Anotaciones"]
    )

    df = load_registros(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if not df.empty:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Vista previa del reporte</div>
            <div style="color:#c9d1d9; margin-top:0.5rem;">
                Período: {fi.strftime('%d/%m/%Y')} — {ff.strftime('%d/%m/%Y')}<br>
                Registros incluidos: <strong>{len(df)}</strong><br>
                Aprobados: <strong>{len(df[df['estado']=='APROBADO'])}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.button("📄 Generar y descargar PDF", type="primary",
              disabled=True, use_container_width=False)
    st.caption("Próximamente disponible — módulo de PDF en construcción")


# ══════════════════════════════════════════════════════════════
# SEGUIMIENTO 1 — REPORTE CANTIDADES
# ══════════════════════════════════════════════════════════════

def page_reporte_cantidades(perfil):
    rol = perfil['rol']
    st.markdown("### Reporte de Cantidades")

    c1, c2, c3 = st.columns(3)
    with c1: fi = st.date_input("Desde", value=date.today()-timedelta(days=15))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3: buscar = st.text_input("🔍 Folio / Actividad")

    df = load_registros(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = (
            df.get('folio','').astype(str).str.contains(buscar, case=False, na=False) |
            df.get('tipo_actividad','').astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("No hay registros para el período seleccionado")
        return

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total registros", len(df))
    with m2: st.metric("Aprobados",       len(df[df['estado']=='APROBADO']))
    with m3: st.metric("Pendientes",      len(df[df['estado'].isin(['BORRADOR','DEVUELTO'])]))
    with m4:
        if 'cantidad' in df.columns:
            total_cant = df['cantidad'].apply(safe_float).sum()
            st.metric("Suma cantidades", f"{total_cant:,.2f}")

    st.divider()

    cols_show = ['folio','usuario_qfield','id_tramo','civ','codigo_elemento',
                 'tipo_actividad','item_pago','item_descripcion',
                 'cantidad','unidad','cant_residente','cant_interventor','estado']
    cols_show = [c for c in cols_show if c in df.columns]

    st.dataframe(
        df[cols_show],
        hide_index=True,
        use_container_width=True,
        column_config={
            'cantidad':         st.column_config.NumberColumn('Cant. Inspector',  format="%.2f"),
            'cant_residente':   st.column_config.NumberColumn('Cant. Residente',  format="%.2f"),
            'cant_interventor': st.column_config.NumberColumn('Cant. Interventor',format="%.2f"),
            'estado':           st.column_config.TextColumn('Estado'),
        }
    )

    # Detalle con fotos
    st.divider()
    st.markdown("#### Detalle con registro fotográfico")

    registros_con_fotos = df[[bool(r.get('foto_1_url') or r.get('foto_2_url'))
                               for _, r in df.iterrows()]] if not df.empty else pd.DataFrame()

    if registros_con_fotos.empty:
        st.caption("No hay registros con fotos en el período seleccionado")
    else:
        for _, reg in registros_con_fotos.head(5).iterrows():
            with st.expander(f"**{reg.get('folio','—')}** · {reg.get('tipo_actividad','—')}", expanded=False):
                st.markdown(f"CIV: `{reg.get('civ','—')}` · Ítem: `{reg.get('item_pago','—')}` · Código elemento: `{reg.get('codigo_elemento','—')}`")
                fotos = [reg.get(f'foto_{i}_url') for i in range(1,6) if reg.get(f'foto_{i}_url')]
                if fotos:
                    fcols = st.columns(min(len(fotos), 4))
                    for i, url in enumerate(fotos[:4]):
                        with fcols[i]:
                            st.image(url, use_column_width=True)

    # CSV
    csv = df[cols_show].to_csv(index=False).encode('utf-8')
    st.download_button(
        "📊 Exportar CSV",
        data=csv,
        file_name=f"Cantidades_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


# ══════════════════════════════════════════════════════════════
# SEGUIMIENTO 2 — MAPA DE OBRA
# ══════════════════════════════════════════════════════════════

def page_mapa(perfil):
    st.markdown("### Mapa de Obra")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: fi = st.date_input("Desde", value=date.today()-timedelta(days=30))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3: estado_f = st.selectbox("Estado", ["Todos","BORRADOR","REVISADO","APROBADO","DEVUELTO"])
    with c4: civ_f = st.text_input("CIV")
    with c5: tramo_f = st.text_input("Tramo")

    if st.button("🔄 Actualizar", use_container_width=False):
        clear_cache()
        st.rerun()

    estados = None if estado_f == "Todos" else [estado_f]
    df = load_registros(estados=estados, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if civ_f and not df.empty:
        df = df[df.get('civ','').astype(str).str.contains(civ_f, case=False, na=False)]
    if tramo_f and not df.empty:
        df = df[df.get('id_tramo','').astype(str).str.contains(tramo_f, case=False, na=False)]

    if df.empty:
        st.info("No hay registros para los filtros seleccionados")
        return

    df_geo = df.dropna(subset=['latitud','longitud']).copy()
    if df_geo.empty:
        st.warning("Los registros del período no tienen coordenadas GPS")
        return

    df_geo['lat'] = pd.to_numeric(df_geo['latitud'],  errors='coerce')
    df_geo['lon'] = pd.to_numeric(df_geo['longitud'], errors='coerce')
    df_geo = df_geo.dropna(subset=['lat','lon'])

    COLOR_MAP = {
        'BORRADOR': '#a0aec0',
        'REVISADO': '#68d391',
        'APROBADO': '#388bfd',
        'DEVUELTO': '#f85149',
    }

    fig = px.scatter_mapbox(
        df_geo,
        lat='lat', lon='lon',
        color='estado',
        color_discrete_map=COLOR_MAP,
        hover_name='tramo_descripcion',
        hover_data={
            'folio':          True,
            'usuario_qfield': True,
            'tipo_actividad': True,
            'item_pago':      True,
            'cantidad':       True,
            'unidad':         True,
            'civ':            True,
            'lat': False, 'lon': False
        },
        size_max=14,
        zoom=12,
        height=560,
        mapbox_style='carto-darkmatter',
    )
    fig.update_traces(marker_size=11)
    fig.update_layout(
        margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            bgcolor='#161b22', bordercolor='#21262d', borderwidth=1,
            font=dict(family='IBM Plex Mono', color='#c9d1d9', size=11),
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"{len(df_geo)} puntos con coordenadas GPS · {len(df) - len(df_geo)} sin coordenadas")


# ══════════════════════════════════════════════════════════════
# SEGUIMIENTO 3 — SEGUIMIENTO PRESUPUESTO
# ══════════════════════════════════════════════════════════════

def page_presupuesto(perfil):
    st.markdown("### Seguimiento de Presupuesto")

    df_ppto = load_presupuesto()
    df_reg  = load_registros()

    if df_ppto.empty:
        st.info("Sin datos de presupuesto. Verifica la tabla `presupuesto` en Supabase.")
        # Demo
        df_ppto = pd.DataFrame({
            'capitulo_num':  [1,1,2,2,3],
            'capitulo':      ['Demolición','Demolición','Pavimentación','Pavimentación','Señalización'],
            'item_pago':     ['1.1','1.2','2.1','2.2','3.1'],
            'item_descripcion':['Demolición concreto','Retiro escombros','Concreto fc28','Asfalto MDC-2','Demarcación vial'],
            'unidad':        ['m3','m3','m3','ton','m2'],
            'cantidad_total':[500,800,1200,900,2000],
            'precio_unitario':[85000,42000,520000,680000,15000],
        })

    # Calcular ejecutado desde registros
    if not df_reg.empty and 'item_pago' in df_reg.columns and 'cant_interventor' in df_reg.columns:
        df_ejec = (df_reg[df_reg['estado']=='APROBADO']
                   .groupby('item_pago')['cant_interventor']
                   .apply(lambda x: pd.to_numeric(x, errors='coerce').sum())
                   .reset_index(name='cantidad_ejecutada'))
        df_ppto = df_ppto.merge(df_ejec, on='item_pago', how='left')
        df_ppto['cantidad_ejecutada'] = df_ppto['cantidad_ejecutada'].fillna(0)
    else:
        df_ppto['cantidad_ejecutada'] = 0

    df_ppto['pct_ejec'] = (df_ppto['cantidad_ejecutada'] / df_ppto['cantidad_total'].replace(0,1) * 100).round(1)
    if 'precio_unitario' in df_ppto.columns:
        df_ppto['valor_total']    = df_ppto['cantidad_total']    * df_ppto['precio_unitario']
        df_ppto['valor_ejecutado']= df_ppto['cantidad_ejecutada']* df_ppto['precio_unitario']

    # Filtros
    c1, c2, c3 = st.columns(3)
    with c1:
        caps = ['Todos'] + sorted(df_ppto['capitulo'].dropna().unique().tolist())
        cap_f = st.selectbox("Capítulo", caps)
    with c2:
        items = ['Todos'] + sorted(df_ppto['item_pago'].dropna().unique().tolist())
        item_f = st.selectbox("Ítem de pago", items)
    with c3:
        buscar = st.text_input("🔍 Actividad")

    df_f = df_ppto.copy()
    if cap_f != 'Todos':   df_f = df_f[df_f['capitulo']==cap_f]
    if item_f != 'Todos':  df_f = df_f[df_f['item_pago']==item_f]
    if buscar:             df_f = df_f[df_f['item_descripcion'].str.contains(buscar, case=False, na=False)]

    if df_f.empty:
        st.info("Sin resultados para los filtros seleccionados")
        return

    # KPIs financieros
    if 'valor_total' in df_f.columns:
        m1, m2, m3, m4 = st.columns(4)
        with m1: kpi("Valor Contrato Filtrado",   f"${df_f['valor_total'].sum():,.0f}", accent_class="kpi-info")
        with m2: kpi("Valor Ejecutado",           f"${df_f['valor_ejecutado'].sum():,.0f}", accent_class="kpi-accent")
        with m3:
            pct = round(df_f['valor_ejecutado'].sum() / df_f['valor_total'].sum() * 100, 1) if df_f['valor_total'].sum() else 0
            kpi("% Ejecución", f"{pct}%", accent_class="kpi-accent" if pct>70 else "kpi-warn")
        with m4: kpi("Ítems", str(len(df_f)))

    st.divider()

    # Tabla
    cols_t = ['capitulo','item_pago','item_descripcion','unidad',
              'cantidad_total','cantidad_ejecutada','pct_ejec']
    if 'valor_total' in df_f.columns:
        cols_t += ['valor_total','valor_ejecutado']
    cols_t = [c for c in cols_t if c in df_f.columns]

    st.dataframe(
        df_f[cols_t],
        hide_index=True,
        use_container_width=True,
        column_config={
            'cantidad_total':     st.column_config.NumberColumn('Cant. Total',    format="%.2f"),
            'cantidad_ejecutada': st.column_config.NumberColumn('Cant. Ejecutada',format="%.2f"),
            'pct_ejec':           st.column_config.ProgressColumn('% Ejec.',     format="%.1f%%", min_value=0, max_value=100),
            'valor_total':        st.column_config.NumberColumn('Valor Total ($)',format="$%,.0f"),
            'valor_ejecutado':    st.column_config.NumberColumn('Valor Ejec. ($)',format="$%,.0f"),
        }
    )

    # Gráfico barras por capítulo
    if 'capitulo' in df_f.columns:
        df_cap = df_f.groupby('capitulo').agg(
            total=('cantidad_total','sum'),
            ejecutado=('cantidad_ejecutada','sum')
        ).reset_index()
        fig = px.bar(df_cap, x='capitulo', y=['total','ejecutado'],
                     barmode='group', height=320,
                     color_discrete_map={'total':'#21262d','ejecutado':'#3fb950'},
                     labels={'value':'Cantidad','capitulo':'Capítulo','variable':''},
                     )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='IBM Plex Sans', color='#8b949e'),
            legend=dict(bgcolor='rgba(0,0,0,0)'),
            xaxis=dict(gridcolor='#1c2333'), yaxis=dict(gridcolor='#1c2333'),
            margin=dict(l=0,r=0,t=20,b=0),
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})


# ══════════════════════════════════════════════════════════════
# SEGUIMIENTO 4 — CURVA S
# ══════════════════════════════════════════════════════════════

def page_curva_s(perfil):
    st.markdown("### Curva S — Avance de Obra")

    df_cs = load_curva_s()

    if df_cs.empty:
        st.info("Sin datos de Curva S. Verifica la tabla `curva_s` en Supabase.")
        # Demo
        semanas = list(range(1, 27))
        pct_prog = [0,2,5,9,14,20,27,35,43,51,58,64,70,75,80,84,87,90,92,94,96,97,98,99,99.5,100]
        pct_ejec = [0,1,3,7,11,16,22,29,36,44,50,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        df_cs = pd.DataFrame({
            'semana': semanas,
            'pct_programado': pct_prog,
            'pct_ejecutado':  pct_ejec,
        })

    # KPIs
    semana_actual = df_cs[df_cs['pct_ejecutado'] > 0]['semana'].max() if 'semana' in df_cs.columns else None

    if semana_actual:
        row = df_cs[df_cs['semana']==semana_actual].iloc[0]
        prog = row.get('pct_programado', 0)
        ejec = row.get('pct_ejecutado', 0)
        delta = round(ejec - prog, 1)

        m1, m2, m3, m4 = st.columns(4)
        with m1: kpi("Semana Actual", str(int(semana_actual)))
        with m2: kpi("Avance Programado", f"{prog:.1f}%")
        with m3: kpi("Avance Ejecutado",  f"{ejec:.1f}%",
                     accent_class="kpi-accent" if delta >= 0 else "kpi-danger")
        with m4: kpi("Desviación", f"{delta:+.1f}%",
                     accent_class="kpi-accent" if delta >= 0 else "kpi-danger")
        st.divider()

    # Gráfico Curva S
    fig = go.Figure()

    # Área programada
    fig.add_trace(go.Scatter(
        x=df_cs['semana'], y=df_cs['pct_programado'],
        mode='lines',
        name='Programado',
        line=dict(color='#388bfd', width=2.5, dash='dot'),
        fill='tozeroy',
        fillcolor='rgba(56,139,253,0.08)',
    ))

    # Ejecutado
    df_ejec = df_cs[df_cs['pct_ejecutado'] > 0]
    if not df_ejec.empty:
        fig.add_trace(go.Scatter(
            x=df_ejec['semana'], y=df_ejec['pct_ejecutado'],
            mode='lines+markers',
            name='Ejecutado',
            line=dict(color='#3fb950', width=3),
            marker=dict(size=7, color='#3fb950', symbol='circle'),
            fill='tozeroy',
            fillcolor='rgba(63,185,80,0.12)',
        ))

        # Línea vertical semana actual
        if semana_actual:
            fig.add_vline(
                x=float(semana_actual),
                line_color='#d29922',
                line_dash='dot',
                line_width=1.5,
                annotation_text=f"Sem. {int(semana_actual)}",
                annotation_font_color='#d29922',
                annotation_font_size=11,
            )

    fig.update_layout(
        height=440,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='IBM Plex Sans', color='#8b949e', size=12),
        legend=dict(
            bgcolor='#161b22', bordercolor='#21262d', borderwidth=1,
            font=dict(family='IBM Plex Mono', color='#c9d1d9', size=11),
            orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0,
        ),
        xaxis=dict(
            title='Semana de ejecución',
            gridcolor='#1c2333', color='#6e7681',
            tickfont=dict(family='IBM Plex Mono'),
        ),
        yaxis=dict(
            title='Avance acumulado (%)',
            gridcolor='#1c2333', color='#6e7681',
            ticksuffix='%', range=[0,105],
            tickfont=dict(family='IBM Plex Mono'),
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#161b22', bordercolor='#21262d',
            font=dict(family='IBM Plex Mono', color='#c9d1d9'),
        ),
        margin=dict(l=0,r=0,t=40,b=0),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})

    # Tabla de avances
    with st.expander("Ver tabla de avances por semana", expanded=False):
        st.dataframe(df_cs, hide_index=True, use_container_width=True,
                     column_config={
                         'semana':           st.column_config.NumberColumn('Semana', format="%d"),
                         'pct_programado':   st.column_config.ProgressColumn('Programado (%)', format="%.1f%%", min_value=0, max_value=100),
                         'pct_ejecutado':    st.column_config.ProgressColumn('Ejecutado (%)',  format="%.1f%%", min_value=0, max_value=100),
                     })


# ══════════════════════════════════════════════════════════════
# TRANSVERSAL — BASE KPI
# ══════════════════════════════════════════════════════════════

def panel_transversal_base(perfil, tipo: str, extra_section=None):
    """
    Base común para Ambiental/SST, Social y PMT.
    tipo: 'ambiental', 'social', 'pmt'
    """
    rol = perfil['rol']

    # Filtros de fecha
    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today()-timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df = load_registros(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    # ── KPIs diarios ──────────────────────────────────────────
    st.markdown("#### KPIs del período")
    kc1, kc2, kc3, kc4 = st.columns(4)

    personal = 0
    maquinaria = 0

    if not df.empty:
        if 'personal_monc' in df.columns:
            personal = pd.to_numeric(df['personal_monc'], errors='coerce').sum()
        if 'maquinaria' in df.columns:
            maquinaria = pd.to_numeric(df['maquinaria'], errors='coerce').sum()

    with kc1: kpi("Personal MONC Reportado", f"{int(personal)}", accent_class="kpi-info")
    with kc2: kpi("Maquinaria", f"{int(maquinaria)}")
    with kc3: kpi("Anotaciones", str(len(df)))
    with kc4:
        if not df.empty and 'cantidad' in df.columns:
            cant = df['cantidad'].apply(safe_float).sum()
            kpi("Cantidades (suma)", f"{cant:,.2f}", accent_class="kpi-accent")
        else:
            kpi("Cantidades", "—")

    st.divider()

    # ── Sección extra (para PMT) ──────────────────────────────
    if extra_section:
        extra_section()
        st.divider()

    # ── Tabla de anotaciones con aprobación escalonada ────────
    st.markdown("#### Registros del período")

    # Determinar config de aprobación según rol
    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    if df.empty:
        st.info("Sin registros para el período")
        return

    if not campos:
        # Solo lectura
        cols = ['folio','usuario_qfield','id_tramo','tipo_actividad','cantidad','unidad','estado']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    df_vis = df[df['estado'].isin(estados_vis)] if estados_vis else df

    if df_vis.empty:
        st.success("✅ No hay registros pendientes")
    else:
        st.markdown(f"**{len(df_vis)} pendiente(s)**")

        for _, reg in df_vis.iterrows():
            with st.expander(f"**{reg.get('folio','—')}** · {reg.get('tipo_actividad','—')}", expanded=False):
                ci, ca = st.columns([2,1])
                with ci:
                    st.markdown(f"""
                    **Inspector:** {reg.get('usuario_qfield','—')} &nbsp;|&nbsp;
                    **Tramo:** {reg.get('id_tramo','—')} &nbsp;|&nbsp;
                    **Unidad:** {reg.get('unidad','—')}
                    """)
                    cant = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cantidad reportada", f"{cant:.2f} {reg.get('unidad','')}")
                    if reg.get('descripcion'):
                        st.info(f"📝 {reg['descripcion']}")

                with ca:
                    campo_cant = campos['campo_cant']
                    campo_obs  = campos['campo_obs']
                    cant_def   = safe_float(reg.get(campo_cant)) or safe_float(reg.get('cantidad')) or 0.0

                    cant_val = st.number_input("Cant. validada", value=float(cant_def),
                                               step=0.01, key=f"tx_cant_{reg['id']}")
                    obs_val  = st.text_area("Observación", key=f"tx_obs_{reg['id']}",
                                            height=70, placeholder="Opcional / Obligatoria para devolver")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅", key=f"tx_apr_{reg['id']}", use_container_width=True, type="primary"):
                            try:
                                sb = get_supabase()
                                upd = {
                                    'estado': estado_apr,
                                    campo_cant: cant_val,
                                    campos['campo_estado']: 'aprobado',
                                    campos['campo_apr']:    perfil['id'],
                                    campos['campo_fecha']:  datetime.now().isoformat(),
                                }
                                if obs_val: upd[campo_obs] = obs_val
                                sb.table('registros').update(upd).eq('id', reg['id']).execute()
                                clear_cache(); st.rerun()
                            except Exception as e:
                                st.error(str(e))
                    with b2:
                        if st.button("↩️", key=f"tx_dev_{reg['id']}", use_container_width=True):
                            if not obs_val:
                                st.error("Escribe observación")
                            else:
                                try:
                                    sb = get_supabase()
                                    sb.table('registros').update({
                                        'estado': 'DEVUELTO',
                                        campos['campo_estado']: 'devuelto',
                                        campo_obs: obs_val,
                                        campos['campo_fecha']: datetime.now().isoformat(),
                                    }).eq('id', reg['id']).execute()
                                    clear_cache(); st.rerun()
                                except Exception as e:
                                    st.error(str(e))


# ══════════════════════════════════════════════════════════════
# TRANSVERSALES
# ══════════════════════════════════════════════════════════════

def page_ambiental(perfil):
    st.markdown("### Componente Ambiental · SST")
    panel_transversal_base(perfil, tipo='ambiental')


def page_social(perfil):
    st.markdown("### Componente Social")
    panel_transversal_base(perfil, tipo='social')


def page_pmt(perfil):
    st.markdown("### Componente PMT")

    def seccion_pmt():
        st.markdown("#### Seguimiento de PMTs")
        # Tabla PMTs activos (requiere tabla `pmts` en Supabase)
        try:
            sb = get_supabase()
            r  = sb.table('pmts').select('*').execute()
            df_pmt = pd.DataFrame(r.data) if r.data else pd.DataFrame()
        except Exception:
            df_pmt = pd.DataFrame()

        if df_pmt.empty:
            st.info("Sin registros de PMTs. Configura la tabla `pmts` en Supabase.")
            # Demo
            df_pmt = pd.DataFrame({
                'codigo':    ['PMT-01','PMT-02','PMT-03'],
                'tramo':     ['Av. Boyacá x Calle 3','Carrera 10 x Calle 1S','Av. Caracas x Calle 14S'],
                'estado':    ['ACTIVO','VENCIDO','ACTIVO'],
                'vigencia':  ['2025-05-01','2025-03-15','2025-06-30'],
                'observaciones':['OK','Renovar','Modificar por desvío'],
            })

        col_a, col_v = st.columns([2,1])
        with col_a:
            st.dataframe(df_pmt, hide_index=True, use_container_width=True)
        with col_v:
            activos = len(df_pmt[df_pmt['estado']=='ACTIVO']) if 'estado' in df_pmt else 0
            vencidos = len(df_pmt[df_pmt['estado']=='VENCIDO']) if 'estado' in df_pmt else 0
            kpi("PMTs Activos",  str(activos),  accent_class="kpi-accent")
            kpi("PMTs Vencidos", str(vencidos), accent_class="kpi-danger" if vencidos > 0 else "")

    panel_transversal_base(perfil, tipo='pmt', extra_section=seccion_pmt)


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

PAGE_MAP = {
    "Estado Actual":              page_estado_actual,
    "Anotaciones":                page_anotaciones,
    "Generar PDF":                page_generar_pdf,
    "Reporte Cantidades":         page_reporte_cantidades,
    "Mapa de Obra":               page_mapa,
    "Seguimiento Presupuesto":    page_presupuesto,
    "Curva S":                    page_curva_s,
    "Componente Ambiental - SST": page_ambiental,
    "Componente Social":          page_social,
    "Componente PMT":             page_pmt,
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
