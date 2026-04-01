"""
app.py
BDO IDU-1556-2025 · App Streamlit
Paneles: Dashboard geografico | Revision de cantidades | Cierre semanal
"""

import os
import math
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime, date, timedelta

# ── Configuración de página ────────────────────────────────────
st.set_page_config(
    page_title="BDO IDU-1556-2025",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  section[data-testid="stSidebar"] { background:#161b2e; }
  .metric-card {
    background:#1e2130; border-radius:10px;
    padding:1rem 1.25rem; border:1px solid #2d3250;
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
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("## 🏗️ BDO IDU-1556-2025")
        st.markdown("##### Sistema de Bitácora Digital de Obra")
        st.markdown("*Contrato IDU-1556-2025 · Grupo 4*")
        st.divider()

        with st.form("login_form"):
            email    = st.text_input("📧 Correo electrónico")
            password = st.text_input("🔒 Contraseña", type="password")
            submit   = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

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
                        st.error("Usuario sin perfil. Contacta al administrador.")
                        return
                    st.session_state['user']   = resp.user
                    st.session_state['perfil'] = perfil.data[0]
                    st.rerun()
            except Exception as e:
                st.error(f"Error de autenticación: {e}")


def logout():
    for key in ['user', 'perfil']:
        st.session_state.pop(key, None)
    st.rerun()


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def get_registros_cached(estados=None, fecha_ini=None, fecha_fin=None):
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


def safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def color_estado(estado):
    colores = {
        'BORRADOR': '🔵',
        'REVISADO': '🟢',
        'APROBADO': '✅',
        'DEVUELTO': '🔴',
    }
    return colores.get(estado, '⚪')


# ══════════════════════════════════════════════════════════════
# PANEL 1 — DASHBOARD GEOGRÁFICO
# ══════════════════════════════════════════════════════════════

def panel_dashboard():
    st.markdown("### 📊 Dashboard de seguimiento en tiempo real")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        fecha_ini = st.date_input("Desde", value=date.today() - timedelta(days=30))
    with c2:
        fecha_fin = st.date_input("Hasta", value=date.today())
    with c3:
        estado_f = st.selectbox("Estado", ["Todos","BORRADOR","REVISADO","APROBADO","DEVUELTO"])
    with c4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    estados = None if estado_f == "Todos" else [estado_f]
    df = get_registros_cached(
        estados=estados,
        fecha_ini=fecha_ini.isoformat(),
        fecha_fin=fecha_fin.isoformat()
    )

    if df.empty:
        st.info("No hay registros para el período seleccionado")
        return

    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Total", len(df))
    with m2: st.metric("Borradores", len(df[df['estado']=='BORRADOR']))
    with m3: st.metric("Revisados", len(df[df['estado']=='REVISADO']))
    with m4: st.metric("Aprobados", len(df[df['estado']=='APROBADO']))
    with m5: st.metric("Devueltos", len(df[df['estado']=='DEVUELTO']))

    st.divider()

    col_mapa, col_der = st.columns([3, 2])

    with col_mapa:
        st.markdown("#### 🗺️ Mapa de frentes")
        df_geo = df.dropna(subset=['latitud','longitud']).copy()

        if not df_geo.empty:
            df_geo['lat'] = pd.to_numeric(df_geo['latitud'],  errors='coerce')
            df_geo['lon'] = pd.to_numeric(df_geo['longitud'], errors='coerce')
            df_geo = df_geo.dropna(subset=['lat','lon'])

            color_map = {
                'BORRADOR': '#a0aec0',
                'REVISADO': '#68d391',
                'APROBADO': '#63b3ed',
                'DEVUELTO': '#fc8181'
            }
            fig = px.scatter_mapbox(
                df_geo,
                lat='lat', lon='lon',
                color='estado',
                color_discrete_map=color_map,
                hover_name='tramo_descripcion',
                hover_data={
                    'folio': True,
                    'usuario_qfield': True,
                    'tipo_actividad': True,
                    'cantidad': True,
                    'unidad': True,
                    'lat': False,
                    'lon': False
                },
                zoom=12,
                height=440,
                mapbox_style='open-street-map'
            )
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin coordenadas GPS en los registros del período")

    with col_der:
        st.markdown("#### 📈 Por actividad")
        if 'tipo_actividad' in df.columns and not df['tipo_actividad'].isna().all():
            df_act = df.groupby(['tipo_actividad','estado']).size().reset_index(name='n')
            fig2 = px.bar(
                df_act, x='n', y='tipo_actividad', color='estado',
                orientation='h', height=220,
                color_discrete_map={
                    'BORRADOR':'#a0aec0','REVISADO':'#68d391',
                    'APROBADO':'#63b3ed','DEVUELTO':'#fc8181'
                }
            )
            fig2.update_layout(
                margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### 📋 Últimos registros")
        cols = ['folio','usuario_qfield','tipo_actividad','cantidad','unidad','estado']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(
            df[cols].head(10),
            hide_index=True,
            use_container_width=True,
            column_config={
                'estado': st.column_config.TextColumn('Estado'),
                'cantidad': st.column_config.NumberColumn('Cantidad', format="%.2f"),
            }
        )


# ══════════════════════════════════════════════════════════════
# PANEL 2 — REVISIÓN DE CANTIDADES
# ══════════════════════════════════════════════════════════════

def panel_revision(perfil):
    rol = perfil['rol']

    if rol in ('supervisor',):
        st.markdown("### 👁️ Vista de registros · Solo lectura")
        df = get_registros_cached()
        if df.empty:
            st.info("Sin registros")
            return
        cols = ['folio','usuario_qfield','id_tramo','tipo_actividad',
                'cantidad','unidad','estado','fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    if rol == 'residente':
        st.markdown("### ✏️ Revisión de cantidades")
        estados_vis  = ['BORRADOR','DEVUELTO']
        estado_apr   = 'REVISADO'
        campo_cant   = 'cant_residente'
        campo_estado = 'estado_residente'
        campo_apr    = 'aprobado_residente'
        campo_fecha  = 'fecha_residente'
        campo_obs    = 'obs_residente'

    elif rol in ('interventor','admin'):
        st.markdown("### ✅ Aprobación de cantidades")
        estados_vis  = ['REVISADO']
        estado_apr   = 'APROBADO'
        campo_cant   = 'cant_interventor'
        campo_estado = 'estado_interventor'
        campo_apr    = 'aprobado_interventor'
        campo_fecha  = 'fecha_interventor'
        campo_obs    = 'obs_interventor'
    else:
        st.warning("Sin permisos para esta sección")
        return

    # Filtros
    c1, c2, c3 = st.columns(3)
    with c1:
        fi = st.date_input("Desde", value=date.today()-timedelta(days=15))
    with c2:
        ff = st.date_input("Hasta", value=date.today())
    with c3:
        buscar = st.text_input("🔍 Buscar folio o actividad")

    df = get_registros_cached(
        estados=estados_vis,
        fecha_ini=fi.isoformat(),
        fecha_fin=ff.isoformat()
    )

    if buscar and not df.empty:
        mask = (
            df.get('folio','').astype(str).str.contains(buscar, case=False, na=False) |
            df.get('tipo_actividad','').astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.success("✅ No hay registros pendientes")
        return

    st.markdown(f"**{len(df)} registro(s) pendiente(s)**")
    st.divider()

    for _, reg in df.iterrows():
        titulo = (
            f"{color_estado(reg.get('estado',''))} "
            f"**{reg.get('folio','—')}** · "
            f"{reg.get('tipo_actividad','—')} · "
            f"{reg.get('tramo_descripcion', reg.get('id_tramo','—'))}"
        )
        with st.expander(titulo, expanded=False):
            ci, ca = st.columns([2,1])

            with ci:
                a, b, c = st.columns(3)
                with a:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield','—')}")
                    st.markdown(f"**Tramo:** {reg.get('id_tramo','—')}")
                    st.markdown(f"**CIV:** {reg.get('civ','—')}")
                with b:
                    st.markdown(f"**Ítem:** {reg.get('item_pago','—')}")
                    st.markdown(f"**Unidad:** {reg.get('unidad','—')}")
                    st.markdown(f"**Fecha:** {str(reg.get('fecha_inicio','—'))[:10]}")
                with c:
                    cant = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cantidad inspector", f"{cant:.2f} {reg.get('unidad','')}")
                    if reg.get('cant_residente'):
                        st.metric("Cant. residente", f"{safe_float(reg.get('cant_residente')):.2f}")

                # Observación del inspector
                if reg.get('descripcion'):
                    st.info(f"📝 {reg.get('descripcion')}")

                # Devolución previa
                if reg.get('obs_residente') and rol == 'interventor':
                    st.warning(f"Obs. residente: {reg.get('obs_residente')}")

                # Fotos
                fotos = [reg.get(f'foto_{i}_url') for i in range(1,6)
                         if reg.get(f'foto_{i}_url')]
                if fotos:
                    st.markdown("**📷 Registro fotográfico:**")
                    fcols = st.columns(min(len(fotos), 3))
                    for i, url in enumerate(fotos[:3]):
                        with fcols[i]:
                            st.image(url, use_column_width=True)

            with ca:
                st.markdown("**Validación:**")
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
                    placeholder="Opcional para aprobar, obligatoria para devolver"
                )

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✅ Aprobar", key=f"apr_{reg['id']}",
                                 use_container_width=True, type="primary"):
                        sb = get_supabase()
                        update = {
                            'estado':      estado_apr,
                            campo_cant:    cant_val,
                            campo_estado:  'aprobado',
                            campo_apr:     perfil['id'],
                            campo_fecha:   datetime.now().isoformat(),
                        }
                        if obs_val:
                            update[campo_obs] = obs_val
                        sb.table('registros').update(update).eq('id', reg['id']).execute()
                        st.success("✅ Aprobado")
                        st.cache_data.clear()
                        st.rerun()

                with b2:
                    if st.button("↩️ Devolver", key=f"dev_{reg['id']}",
                                 use_container_width=True):
                        if not obs_val:
                            st.error("Escribe una observación")
                        else:
                            sb = get_supabase()
                            sb.table('registros').update({
                                'estado':     'DEVUELTO',
                                campo_estado: 'devuelto',
                                campo_obs:    obs_val,
                                campo_fecha:  datetime.now().isoformat(),
                            }).eq('id', reg['id']).execute()
                            st.warning("↩️ Devuelto")
                            st.cache_data.clear()
                            st.rerun()


# ══════════════════════════════════════════════════════════════
# PANEL 3 — CIERRE SEMANAL
# ══════════════════════════════════════════════════════════════

def panel_cierre(perfil):
    rol = perfil['rol']
    st.markdown("### 📄 Cierre semanal y exportación")

    c1, c2 = st.columns(2)
    with c1:
        hoy   = date.today()
        lunes = hoy - timedelta(days=hoy.weekday())
        fi    = st.date_input("Inicio de semana", value=lunes)
    with c2:
        ff    = st.date_input("Fin de semana", value=lunes+timedelta(days=6))

    df = get_registros_cached(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if df.empty:
        st.info("No hay registros para esta semana")
        return

    st.markdown(f"#### Semana {fi.strftime('%d/%m')} – {ff.strftime('%d/%m/%Y')}")

    # Resumen de estados
    col_tbl, col_stats = st.columns([3,1])

    with col_tbl:
        cols = ['folio','id_tramo','tipo_actividad','item_pago','item_descripcion',
                'unidad','cantidad','cant_residente','cant_interventor','estado']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(
            df[cols],
            hide_index=True,
            use_container_width=True,
            column_config={
                'cantidad':         st.column_config.NumberColumn('Cant. inspector',  format="%.2f"),
                'cant_residente':   st.column_config.NumberColumn('Cant. residente',  format="%.2f"),
                'cant_interventor': st.column_config.NumberColumn('Cant. interventor',format="%.2f"),
            }
        )

    with col_stats:
        total      = len(df)
        aprobados  = len(df[df['estado']=='APROBADO'])
        revisados  = len(df[df['estado']=='REVISADO'])
        pendientes = len(df[df['estado'].isin(['BORRADOR','DEVUELTO'])])
        pct        = round(aprobados/total*100) if total > 0 else 0

        st.metric("Total registros",  total)
        st.metric("Aprobados",        aprobados)
        st.metric("Revisados",        revisados)
        st.metric("Pendientes",       pendientes)
        st.progress(pct/100, text=f"{pct}% aprobado")

    st.divider()

    col_xl, col_cierre = st.columns(2)

    with col_xl:
        csv = df[cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Descargar CSV",
            data=csv,
            file_name=f"BDO_IDU1556_{fi.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col_cierre:
        if rol in ('interventor','admin'):
            df_apr = df[df['estado']=='APROBADO']
            if df_apr.empty:
                st.warning("No hay registros aprobados para cerrar")
            else:
                if st.button(
                    f"✅ Cerrar semana ({len(df_apr)} registros aprobados)",
                    use_container_width=True,
                    type="primary"
                ):
                    sb     = get_supabase()
                    cierre = sb.table('cierres_semanales').insert({
                        'contrato_id':         'IDU-1556-2025',
                        'semana_inicio':        fi.isoformat(),
                        'semana_fin':           ff.isoformat(),
                        'total_registros':      len(df_apr),
                        'estado':              'APROBADO',
                        'aprobado_interventor': perfil['id'],
                        'fecha_int':           datetime.now().isoformat(),
                    }).execute()

                    if cierre.data:
                        cierre_id = cierre.data[0]['id']
                        links = [{'cierre_id': cierre_id, 'registro_id': r}
                                 for r in df_apr['id'].tolist()]
                        sb.table('cierre_registros').insert(links).execute()
                        st.success(f"✅ Semana cerrada — {len(df_apr)} registros")
                        st.cache_data.clear()
        else:
            st.info("Solo el interventor puede cerrar la semana")


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════

def sidebar(perfil):
    with st.sidebar:
        st.markdown("### 🏗️ BDO IDU-1556-2025")
        st.markdown(f"**{perfil['nombre']}**")
        st.markdown(f"*{perfil['empresa']}*")

        rol_labels = {
            'admin':      '⚙️ Administrador',
            'residente':  '✏️ Residente de obra',
            'interventor':'✅ Interventor',
            'supervisor': '👁️ Supervisor IDU',
            'inspector':  '📋 Inspector',
        }
        st.markdown(f"`{rol_labels.get(perfil['rol'], perfil['rol'])}`")
        st.divider()

        rol = perfil['rol']
        opciones = ["📊 Dashboard"]

        if rol in ('residente','interventor','admin','supervisor'):
            opciones.append("✏️ Revisión de cantidades")
        if rol in ('interventor','admin'):
            opciones.append("📄 Cierre semanal")

        panel = st.radio("", opciones, label_visibility="collapsed")

        st.divider()

        # Resumen rápido
        df_q = get_registros_cached()
        if not df_q.empty:
            st.markdown("**Resumen general**")
            for estado, icon in [
                ('BORRADOR','🔵'),('REVISADO','🟢'),
                ('APROBADO','✅'),('DEVUELTO','🔴')
            ]:
                n = len(df_q[df_q['estado']==estado])
                if n > 0:
                    st.markdown(f"{icon} {estado}: **{n}**")

        st.divider()
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            logout()

    return panel


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    if 'user' not in st.session_state:
        login()
        return

    perfil = st.session_state['perfil']
    panel  = sidebar(perfil)

    if "Dashboard"  in panel:
        panel_dashboard()
    elif "Revisión" in panel:
        panel_revision(perfil)
    elif "Cierre"   in panel:
        panel_cierre(perfil)


if __name__ == '__main__':
    main()
