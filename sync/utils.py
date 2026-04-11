import math


def safe(val):
    if val is None:
        return None
    try:
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return None if s in ('', 'nan', 'None', 'NaT') else s


def safe_num(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def coords_from_geom(row):
    lat = lon = None
    geom = row.get('geometry') or row.get('geom')
    if geom is not None:
        try:
            if hasattr(geom, 'x') and hasattr(geom, 'y'):
                lon, lat = geom.x, geom.y
        except Exception:
            pass
    return lat, lon
