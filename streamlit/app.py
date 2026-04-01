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

# ── CSS personalizado ──────────────────────────────────────────
st.markdown("""
<style>
  .stApp { background-color: #0f1117; }
  .metric-card {
    background: #1e2130;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    border: 1px solid #2d3250;
  }
  .badge-borrador  { background:#2d3250; color:#a0aec0; padding:2px 10px; border-radius:10px; font-size:12px; }
  .badge-revisado  { background:#1a3a2a; color:#68d391; padding:2px 10px; border-radius:10px; font-size:12px; }
  .badge-aprobado  { background:#1a2a3a; color:#63b3ed; padding:2px 10px; border-radius:10px; font-size:12px; }
  .badge-devuelto  { background:#3a1a1a; color:#fc8181; padding:2px 10px; border-radius:10px; font-size:12px; }
  div[data-testid="stSidebarContent"] { background:#161b2e; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# CONEXIÓN SUPABASE
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase():
    url = os.environ.get('SUPABASE_URL', st.secrets.get('SUPABASE_URL', ''))
    key = os.environ.get('SUPABASE_KEY', st.secrets.get('SUPABASE_KEY', ''))
    return create_client(url, key)


# ══════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════

def login():
    """Pantalla de login"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🏗️ BDO IDU-1556-2025")
        st.markdown("##### Bitácora Digital de Obra")
        st.divider()

        with st.form("login_form"):
            email    = st.text_input("Correo electrónico")
            password = st.text_input("Contraseña", type="password")
            submit   = st.form_submit_button("Ingresar", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("Ingresa correo y contraseña")
                return

            try:
                sb   = get_supabase()
                resp = sb.auth.sign_in_with_password({"email": email, "password": password})

                if resp.user:
                    # Obtiene perfil del usuario
                    perfil = sb.table('perfiles').select('*').eq('id', resp.user.id).execute()

                    if not perfil.data:
                        st.error("Usuario sin perfil configurado. Contacta al administrador.")
                        return

                    st.session_state['user']   = resp.user
                    st.session_state['perfil'] = perfil.data[0]
                    st.session_state['token']  = resp.session.access_token
                    st.rerun()

            except Exception as e:
                st.error(f"Error de autenticación: {e}")


def logout():
    for key in ['user', 'perfil', 'token']:
        st.session_state.pop(key, None)
    st.rerun()


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def get_registros(filtros=None):
    """Carga registros desde Supabase con filtros opcionales"""
    sb     = get_supabase()
    query  = sb.table('registros').select('*')

    if filtros:
        if filtros.get('estado'):
            query = query.eq('estado', filtros['estado'])
        if filtros.get('estados'):
            query = query.in_('estado', filtros['estados'])
        if filtros.get('fecha_ini'):
            query = query.gte('fecha_creacion', filtros['fecha_ini'].isoformat())
        if filtros.get('fecha_fin'):
            query = query.lte('fecha_creacion', filtros['fecha_fin'].isoformat())
        if filtros.get('id_tramo'):
            query = query.eq('id_tramo', filtros['id_tramo'])
        if filtros.get('tipo_actividad'):
            query = query.eq('tipo_actividad', filtros['tipo_actividad'])

    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def badge_estado(estado):
    colores = {
        'BORRADOR':  ('🔵', '#2d3250', '#a0aec0'),
        'REVISADO':  ('🟢', '#1a3a2a', '#68d391'),
        'APROBADO':  ('✅', '#1a2a3a', '#63b3ed'),
        'DEVUELTO':  ('🔴', '#3a1a1a', '#fc8181'),
    }
    e, bg, fg = colores.get(estado, ('⚪', '#2d3250', '#a0aec0'))
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:10px;font-size:12px">{e} {estado}</span>'


def safe_float(val):
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════
# PANEL 1 — DASHBOARD GEOGRÁFICO
# ══════════════════════════════════════════════════════════════

def panel_dashboard(perfil):
    st.markdown("### 📊 Dashboard de seguimiento")

    # Filtros superiores
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        fecha_ini = st.date_input("Desde", value=date.today() - timedelta(days=30))
    with col2:
        fecha_fin = st.date_input("Hasta", value=date.today())
    with col3:
        estado_f = st.selectbox("Estado", ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"])
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", use_container_width=True):
            st.cache_data.clear()

    # Carga datos
    filtros = {'fecha_ini': fecha_ini, 'fecha_fin': fecha_fin}
    if estado_f != "Todos":
        filtros['estado'] = estado_f

    df = get_registros(filtros)

    if df.empty:
        st.info("No hay registros para el período seleccionado")
        return

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total registros", len(df))
    with c2:
        st.metric("Aprobados", len(df[df['estado'] == 'APROBADO']))
    with c3:
        st.metric("En revisión", len(df[df['estado'].isin(['BORRADOR', 'REVISADO'])]))
    with c4:
        st.metric("Devueltos", len(df[df['estado'] == 'DEVUELTO']))

    st.divider()

    col_mapa, col_graf = st.columns([3, 2])

    with col_mapa:
        st.markdown("#### 🗺️ Mapa de registros")
        df_geo = df.dropna(subset=['latitud', 'longitud'])

        if not df_geo.empty:
            # Color por estado
            color_map = {
                'BORRADOR': '#a0aec0',
                'REVISADO': '#68d391',
                'APROBADO': '#63b3ed',
                'DEVUELTO': '#fc8181'
            }
            df_geo = df_geo.copy()
            df_geo['color'] = df_geo['estado'].map(color_map).fillna('#a0aec0')
            df_geo['lat']   = pd.to_numeric(df_geo['latitud'],  errors='coerce')
            df_geo['lon']   = pd.to_numeric(df_geo['longitud'], errors='coerce')
            df_geo          = df_geo.dropna(subset=['lat', 'lon'])

            fig = px.scatter_mapbox(
                df_geo,
                lat='lat', lon='lon',
                color='estado',
                color_discrete_map=color_map,
                hover_data=['folio', 'usuario_qfield', 'tipo_actividad', 'cantidad', 'unidad'],
                hover_name='tramo_descripcion',
                zoom=12,
                height=420,
                mapbox_style='carto-darkmatter'
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(bgcolor='rgba(0,0,0,0)', font_color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin coordenadas GPS en los registros del período")

    with col_graf:
        st.markdown("#### 📈 Avance por actividad")
        if 'tipo_actividad' in df.columns:
            df_act = df.groupby(['tipo_actividad', 'estado']).size().reset_index(name='count')
            if not df_act.empty:
                fig2 = px.bar(
                    df_act,
                    x='count', y='tipo_actividad',
                    color='estado',
                    orientation='h',
                    color_discrete_map={
                        'BORRADOR': '#a0aec0',
                        'REVISADO': '#68d391',
                        'APROBADO': '#63b3ed',
                        'DEVUELTO': '#fc8181'
                    },
                    height=200
                )
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    margin=dict(l=0, r=0, t=0, b=0),
                    legend=dict(bgcolor='rgba(0,0,0,0)')
                )
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown("#### 📋 Últimos registros")
        cols_show = ['folio', 'usuario_qfield', 'tipo_actividad', 'cantidad', 'unidad', 'estado']
        cols_show = [c for c in cols_show if c in df.columns]
        st.dataframe(
            df[cols_show].head(8),
            hide_index=True,
            use_container_width=True
        )


# ══════════════════════════════════════════════════════════════
# PANEL 2 — REVISIÓN DE CANTIDADES
# ══════════════════════════════════════════════════════════════

def panel_revision(perfil):
    rol = perfil['rol']

    if rol == 'residente':
        st.markdown("### ✏️ Revisión de cantidades · Residente")
        estados_visibles = ['BORRADOR', 'DEVUELTO']
        label_accion     = "Aprobar como revisado"
        estado_aprueba   = "REVISADO"
        campo_cant       = "cant_residente"
        campo_estado     = "estado_residente"
        campo_aprobado   = "aprobado_residente"
        campo_fecha      = "fecha_residente"
        campo_obs        = "obs_residente"

    elif rol == 'interventor':
        st.markdown("### ✅ Aprobación de cantidades · Interventor")
        estados_visibles = ['REVISADO']
        label_accion     = "Aprobar definitivamente"
        estado_aprueba   = "APROBADO"
        campo_cant       = "cant_interventor"
        campo_estado     = "estado_interventor"
        campo_aprobado   = "aprobado_interventor"
        campo_fecha      = "fecha_interventor"
        campo_obs        = "obs_interventor"
    else:
        st.info("Solo residentes e interventores pueden validar cantidades")
        return

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_ini = st.date_input("Desde", value=date.today() - timedelta(days=15))
    with col2:
        fecha_fin = st.date_input("Hasta", value=date.today())
    with col3:
        buscar = st.text_input("Buscar folio o actividad")

    df = get_registros({'estados': estados_visibles, 'fecha_ini': fecha_ini, 'fecha_fin': fecha_fin})

    if buscar:
        mask = (
            df['folio'].str.contains(buscar, case=False, na=False) |
            df['tipo_actividad'].str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.success(f"✅ No hay registros pendientes de {'revisión' if rol == 'residente' else 'aprobación'}")
        return

    st.markdown(f"**{len(df)} registro(s) pendiente(s)**")
    st.divider()

    for _, reg in df.iterrows():
        with st.expander(
            f"📋 {reg.get('folio','—')}  ·  {reg.get('tipo_actividad','—')}  ·  "
            f"{reg.get('tramo_descripcion', reg.get('id_tramo','—'))}",
            expanded=False
        ):
            col_info, col_accion = st.columns([2, 1])

            with col_info:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield','—')}")
                    st.markdown(f"**Tramo:** {reg.get('id_tramo','—')}")
                    st.markdown(f"**CIV:** {reg.get('civ','—')}")
                with c2:
                    st.markdown(f"**Ítem:** {reg.get('item_pago','—')}")
                    st.markdown(f"**Descripción:** {reg.get('item_descripcion','—')}")
                    st.markdown(f"**Fecha:** {str(reg.get('fecha_inicio','—'))[:10]}")
                with c3:
                    cant_orig = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cantidad reportada", f"{cant_orig} {reg.get('unidad','')}")
                    st.markdown(f"**Observación inspector:** {reg.get('descripcion','—')}")

                # Fotos
                fotos = [reg.get(f'foto_{i}_url') for i in range(1, 6) if reg.get(f'foto_{i}_url')]
                if fotos:
                    st.markdown("**Registro fotográfico:**")
                    cols_foto = st.columns(min(len(fotos), 3))
                    for i, url in enumerate(fotos[:3]):
                        with cols_foto[i]:
                            st.image(url, use_column_width=True)

            with col_accion:
                st.markdown("**Validación:**")
                key_cant = f"cant_{reg['id']}"
                key_obs  = f"obs_{reg['id']}"
                key_dev  = f"dev_{reg['id']}"
                key_apr  = f"apr_{reg['id']}"

                cant_val = st.number_input(
                    "Cantidad validada",
                    value=float(safe_float(reg.get(campo_cant)) or safe_float(reg.get('cantidad')) or 0),
                    step=0.01,
                    key=key_cant
                )
                obs_val = st.text_area("Observación", key=key_obs, height=80)

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.button("✅ Aprobar", key=key_apr, use_container_width=True, type="primary"):
                        sb = get_supabase()
                        sb.table('registros').update({
                            'estado':        estado_aprueba,
                            campo_cant:      cant_val,
                            campo_estado:    'aprobado',
                            campo_aprobado:  perfil['id'],
                            campo_fecha:     datetime.now().isoformat(),
                            campo_obs:       obs_val or None,
                        }).eq('id', reg['id']).execute()
                        st.success("✅ Aprobado")
                        st.cache_data.clear()
                        st.rerun()

                with col_btn2:
                    if st.button("↩️ Devolver", key=key_dev, use_container_width=True):
                        if not obs_val:
                            st.error("Escribe una observación antes de devolver")
                        else:
                            sb = get_supabase()
                            sb.table('registros').update({
                                'estado':     'DEVUELTO',
                                campo_estado: 'devuelto',
                                campo_obs:    obs_val,
                                campo_fecha:  datetime.now().isoformat(),
                            }).eq('id', reg['id']).execute()
                            st.warning("↩️ Devuelto al inspector")
                            st.cache_data.clear()
                            st.rerun()


# ══════════════════════════════════════════════════════════════
# PANEL 3 — CIERRE SEMANAL Y EXPORTACIÓN
# ══════════════════════════════════════════════════════════════

def panel_cierre(perfil):
    rol = perfil['rol']
    st.markdown("### 📄 Cierre semanal y exportación")

    # Selector de semana
    col1, col2 = st.columns(2)
    with col1:
        hoy      = date.today()
        lunes    = hoy - timedelta(days=hoy.weekday())
        semana_i = st.date_input("Inicio de semana", value=lunes)
    with col2:
        semana_f = st.date_input("Fin de semana", value=lunes + timedelta(days=6))

    df = get_registros({'fecha_ini': semana_i, 'fecha_fin': semana_f})

    if df.empty:
        st.info("No hay registros para esta semana")
        return

    # Resumen de cantidades
    st.markdown(f"#### Semana {semana_i.strftime('%d/%m')} – {semana_f.strftime('%d/%m/%Y')}")

    col_res, col_est = st.columns([3, 1])

    with col_res:
        # Tabla resumen por ítem
        cols_tabla = ['folio', 'id_tramo', 'tipo_actividad', 'item_pago',
                      'item_descripcion', 'unidad', 'cantidad',
                      'cant_residente', 'cant_interventor', 'estado']
        cols_tabla = [c for c in cols_tabla if c in df.columns]

        st.dataframe(
            df[cols_tabla],
            hide_index=True,
            use_container_width=True,
            column_config={
                'estado': st.column_config.TextColumn('Estado'),
                'cantidad': st.column_config.NumberColumn('Cant. inspector', format="%.2f"),
                'cant_residente': st.column_config.NumberColumn('Cant. residente', format="%.2f"),
                'cant_interventor': st.column_config.NumberColumn('Cant. interventor', format="%.2f"),
            }
        )

    with col_est:
        total       = len(df)
        aprobados   = len(df[df['estado'] == 'APROBADO'])
        revisados   = len(df[df['estado'] == 'REVISADO'])
        pendientes  = len(df[df['estado'].isin(['BORRADOR', 'DEVUELTO'])])

        st.metric("Total", total)
        st.metric("Aprobados", aprobados)
        st.metric("Revisados", revisados)
        st.metric("Pendientes", pendientes)

        pct = round(aprobados / total * 100) if total > 0 else 0
        st.progress(pct / 100, text=f"{pct}% aprobado")

    st.divider()

    # Exportar a Excel
    col_xl, col_pdf, col_cierre = st.columns(3)

    with col_xl:
        if st.button("📊 Exportar Excel", use_container_width=True):
            excel_buf = df[cols_tabla].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Descargar CSV",
                data=excel_buf,
                file_name=f"BDO_IDU1556_{semana_i.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with col_pdf:
        if st.button("📄 Generar bitácora PDF", use_container_width=True):
            st.info("PDF en desarrollo — próxima versión")

    with col_cierre:
        if rol == 'interventor':
            aprobados_semana = df[df['estado'] == 'APROBADO']
            if len(aprobados_semana) == 0:
                st.warning("No hay registros aprobados para cerrar")
            else:
                if st.button(
                    f"✅ Cerrar semana ({len(aprobados_semana)} reg.)",
                    use_container_width=True,
                    type="primary"
                ):
                    sb = get_supabase()
                    # Crea el cierre semanal
                    cierre = sb.table('cierres_semanales').insert({
                        'contrato_id':         'IDU-1556-2025',
                        'semana_inicio':        semana_i.isoformat(),
                        'semana_fin':           semana_f.isoformat(),
                        'total_registros':      len(aprobados_semana),
                        'estado':              'APROBADO',
                        'aprobado_interventor': perfil['id'],
                        'fecha_int':           datetime.now().isoformat(),
                    }).execute()

                    if cierre.data:
                        cierre_id = cierre.data[0]['id']
                        # Vincula registros al cierre
                        links = [{'cierre_id': cierre_id, 'registro_id': r} 
                                 for r in aprobados_semana['id'].tolist()]
                        sb.table('cierre_registros').insert(links).execute()
                        st.success(f"✅ Semana cerrada — {len(aprobados_semana)} registros")
                        st.cache_data.clear()
        else:
            st.info("Solo el interventor puede cerrar la semana")


# ══════════════════════════════════════════════════════════════
# SIDEBAR Y NAVEGACIÓN
# ══════════════════════════════════════════════════════════════

def sidebar(perfil):
    with st.sidebar:
        st.markdown(f"### 🏗️ BDO IDU-1556-2025")
        st.markdown(f"**{perfil['nombre']}**")
        st.markdown(f"*{perfil['empresa']}*")
        st.markdown(f"`{perfil['rol'].upper()}`")
        st.divider()

        rol = perfil['rol']

        opciones = ["📊 Dashboard"]
        if rol in ('residente', 'interventor'):
            opciones.append("✏️ Revisión de cantidades")
        if rol in ('interventor', 'residente'):
            opciones.append("📄 Cierre semanal")

        panel = st.radio("Navegación", opciones, label_visibility="collapsed")

        st.divider()

        # Métricas rápidas en sidebar
        df_quick = get_registros()
        if not df_quick.empty:
            st.markdown("**Resumen general**")
            for estado, color in [('BORRADOR','🔵'),('REVISADO','🟢'),('APROBADO','✅'),('DEVUELTO','🔴')]:
                n = len(df_quick[df_quick['estado'] == estado])
                if n > 0:
                    st.markdown(f"{color} {estado}: **{n}**")

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

    if "Dashboard" in panel:
        panel_dashboard(perfil)
    elif "Revisión" in panel:
        panel_revision(perfil)
    elif "Cierre" in panel:
        panel_cierre(perfil)


if __name__ == '__main__':
    main()
