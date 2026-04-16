"""
config.py — Constantes globales de la aplicación BDO IDU-1556-2025
Roles, navegación, paleta de colores y configuración de aprobaciones.
"""

# ══════════════════════════════════════════════════════════════
# ROLES
# ══════════════════════════════════════════════════════════════
# operativo    → inspectores de campo; crean registros en QField y
#                realizan anotaciones generales (solo lectura en reportes)
# obra         → residentes de obra; revisan y aprueban nivel 1
# interventoria→ interventoría IDU; aprueban definitivamente nivel 2
# supervision  → supervisión IDU; solo lectura
# admin        → administrador total del sistema

ROL_LABELS: dict[str, str] = {
    'operativo':     'Inspector de Campo',
    'obra':          'Residente de Obra',
    'interventoria': 'Interventoría IDU',
    'supervision':   'Supervisión IDU',
    'admin':         'Administrador',
}

# ══════════════════════════════════════════════════════════════
# CONTROL DE ACCESO POR PÁGINA
# ══════════════════════════════════════════════════════════════

# Todos los roles autenticados
_TODOS = ['operativo', 'obra', 'interventoria', 'supervision', 'admin']

# Solo gestión (operativo no accede a vistas financieras,
# mapas de ejecución ni generación de informes)
_GESTION = ['obra', 'interventoria', 'supervision', 'admin']

# operativo ve sus propios datos (RLS filtra por creado_por);
# obra+ ven todos los registros para revisar/aprobar.
# formulario_pmt no tiene filtro por creado_por en RLS → todos ven todos.


NAV_ACCESS: dict[str, list[str]] = {
    # ── General ──────────────────────────────────────────────
    "Estado Actual":              _TODOS,
    "Anotaciones":                _TODOS,
    "Anotaciones Diario":         _TODOS,
    # Solo gestión: vistas financieras y de infraestructura a nivel proyecto
    "Mapa Ejecución":             _GESTION,
    "Seguimiento Presupuesto":    _GESTION,
    "Generar Informe":            _GESTION,
    # ── Reportes ─────────────────────────────────────────────
    # operativo ve sus propios registros (RLS: creado_por = auth.uid())
    # obra+ ven todos para el flujo de revisión y aprobación
    "Reporte Cantidades":         _TODOS,
    # ── Componentes Transversales ─────────────────────────────
    # Mismo patrón de RLS que Reporte Cantidades
    "Componente Ambiental - SST": _TODOS,
    "Componente Social":          _TODOS,
    # formulario_pmt: RLS sin filtro por creado_por → todos ven todos los PMTs
    "Componente PMT":             _TODOS,
    "Seguimiento PMTs":           _TODOS,
}

# ══════════════════════════════════════════════════════════════
# ESTRUCTURA DE NAVEGACIÓN
# ══════════════════════════════════════════════════════════════

NAV_CATEGORIES: list[dict] = [
    {
        "label":     "General",
        "highlight": False,
        "pages":     ["Estado Actual", "Mapa Ejecución",
                      "Seguimiento Presupuesto"],
    },
    {
        "label":     "Reportes",
        "highlight": True,
        "pages":     ["Anotaciones", "Anotaciones Diario",
                      "Reporte Cantidades"],
    },
    {
        "label":     "Componentes Transversales",
        "highlight": True,
        "pages":     ["Componente Ambiental - SST",
                      "Componente Social",
                      "Componente PMT",
                      "Seguimiento PMTs"],
    },
    {
        "label":     "Informe",
        "highlight": True,
        "pages":     ["Generar Informe"],
    },
]

# Acento de color por página (usado en section_badge y KPI cards)
PAGE_COLOR: dict[str, str] = {
    "Estado Actual":              "blue",
    "Anotaciones":                "purple",
    "Anotaciones Diario":         "purple",
    "Generar Informe":            "teal",
    "Mapa Ejecución":             "teal",
    "Seguimiento Presupuesto":    "orange",
    "Reporte Cantidades":         "blue",
    "Componente Ambiental - SST": "green",
    "Componente Social":          "orange",
    "Componente PMT":             "purple",
    "Seguimiento PMTs":           "red",
}

# ══════════════════════════════════════════════════════════════
# FLUJO DE APROBACIÓN ESCALONADA
# ══════════════════════════════════════════════════════════════
# Formato: rol → (estados_visibles, estado_al_aprobar, dict_campos)
# estados_visibles=None → solo lectura (sin botones de acción)

APROBACION_CONFIG: dict[str, tuple] = {
    # operativo: solo lectura, sin panel de aprobación
    'operativo':     (None, None, None),
    # obra (residente): nivel 1 — revisa BORRADOR/DEVUELTO → REVISADO
    'obra': (
        ['BORRADOR', 'DEVUELTO'],
        'REVISADO',
        {
            'campo_cant':   'cant_residente',
            'campo_estado': 'estado_residente',
            'campo_apr':    'aprobado_residente',
            'campo_fecha':  'fecha_residente',
            'campo_obs':    'obs_residente',
        },
    ),
    # interventoria: nivel 2 — aprueba definitivamente REVISADO → APROBADO
    'interventoria': (
        ['REVISADO'],
        'APROBADO',
        {
            'campo_cant':   'cant_interventor',
            'campo_estado': 'estado_interventor',
            'campo_apr':    'aprobado_interventor',
            'campo_fecha':  'fecha_interventor',
            'campo_obs':    'obs_interventor',
        },
    ),
    # supervision: solo lectura
    'supervision':   (None, None, None),
    # admin: mismos permisos que interventoria (aprobación nivel 2)
    'admin': (
        ['REVISADO'],
        'APROBADO',
        {
            'campo_cant':   'cant_interventor',
            'campo_estado': 'estado_interventor',
            'campo_apr':    'aprobado_interventor',
            'campo_fecha':  'fecha_interventor',
            'campo_obs':    'obs_interventor',
        },
    ),
}
