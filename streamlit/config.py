"""
config.py — Constantes globales de la aplicación BDO IDU-1556-2025
Roles, navegación, paleta de colores y configuración de aprobaciones.
"""

# ══════════════════════════════════════════════════════════════
# ROLES
# ══════════════════════════════════════════════════════════════

ROL_LABELS: dict[str, str] = {
    'inspector':   'Inspector de Campo',
    'obra':        'Personal de Obra',
    'residente':   'Residente de Obra',
    'coordinador': 'Coordinador de Obra',
    'interventor': 'Interventor IDU',
    'supervisor':  'Supervisor IDU',
    'admin':       'Administrador',
}

# ══════════════════════════════════════════════════════════════
# CONTROL DE ACCESO POR PÁGINA
# ══════════════════════════════════════════════════════════════

_TODOS = ['inspector', 'obra', 'residente', 'coordinador',
          'interventor', 'supervisor', 'admin']
_GESTION = ['residente', 'coordinador', 'interventor', 'supervisor', 'admin']

NAV_ACCESS: dict[str, list[str]] = {
    # ── General ──────────────────────────────────────────────
    "Estado Actual":              _TODOS,
    "Anotaciones":                _TODOS,
    "Generar PDF":                _GESTION,
    "Mapa de Obra":               _GESTION,
    "Seguimiento Presupuesto":    _GESTION,
    # ── Reportes de Cantidades ────────────────────────────────
    "Reporte Cantidades":         _GESTION,
    # ── Reportes de Componentes Transversales ─────────────────
    "Componente Ambiental - SST": _GESTION,
    "Componente Social":          _GESTION,
    "Componente PMT":             _GESTION,
    # ── Seguimiento de PMTs ───────────────────────────────────
    "Seguimiento PMTs":           _GESTION,
}

# ══════════════════════════════════════════════════════════════
# ESTRUCTURA DE NAVEGACIÓN
# ══════════════════════════════════════════════════════════════

NAV_CATEGORIES: list[dict] = [
    {
        "label":     "General",
        "highlight": False,
        "pages":     ["Estado Actual", "Anotaciones", "Generar PDF",
                      "Mapa de Obra", "Seguimiento Presupuesto"],
    },
    {
        "label":     "Reportes de Cantidades",
        "highlight": True,
        "pages":     ["Reporte Cantidades"],
    },
    {
        "label":     "Componentes Transversales",
        "highlight": True,
        "pages":     ["Componente Ambiental - SST",
                      "Componente Social",
                      "Componente PMT"],
    },
    {
        "label":     "Seguimiento de PMTs",
        "highlight": True,
        "pages":     ["Seguimiento PMTs"],
    },
]

# Acento de color por página (usado en section_badge y KPI cards)
PAGE_COLOR: dict[str, str] = {
    "Estado Actual":              "blue",
    "Anotaciones":                "purple",
    "Generar PDF":                "teal",
    "Mapa de Obra":               "teal",
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
    'inspector':   (None, None, None),
    'obra':        (None, None, None),
    'residente':   (
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
    'coordinador': (
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
    'interventor': (
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
    'supervisor':  (None, None, None),
    'admin':       (
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
