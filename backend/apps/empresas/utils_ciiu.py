import os
import json
import re
import unicodedata

_catalog = None

def get_catalog():
    global _catalog
    if _catalog is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "data", "ciiu_768_catalog.json")
        with open(json_path, "r", encoding="utf-8") as f:
            _catalog = json.load(f)
    return _catalog

def expand(raw, catalog):
    try:
        sector = catalog["sectors"][raw["s"]] if raw["s"] < len(catalog["sectors"]) else ""
    except (IndexError, KeyError):
        sector = ""

    try:
        division = catalog["divisions"][raw["div"]] if raw["div"] < len(catalog["divisions"]) else ""
    except (IndexError, KeyError):
        division = ""

    try:
        grupo = catalog["grupos"][raw["g"]] if raw["g"] < len(catalog["grupos"]) else ""
    except (IndexError, KeyError):
        grupo = ""

    return {
        "codigo_768": raw["c"],
        "clase_riesgo": raw["r"],
        "ciiu_rev4": raw["ciiu"],
        "descripcion": raw["d"],
        "sector": sector,
        "division": division,
        "grupo": grupo,
    }

def buscar_por_codigo_768(codigo):
    catalog = get_catalog()
    codigo_clean = str(codigo).strip()
    for raw in catalog["codes"]:
        if raw["c"] == codigo_clean:
            return expand(raw, catalog)
    return None

def buscar_multiples_por_codigo_768(codigos):
    catalog = get_catalog()
    set_codigos = {str(c).strip() for c in codigos}
    result = []
    for raw in catalog["codes"]:
        if raw["c"] in set_codigos:
            result.append(expand(raw, catalog))
    return result

SECTOR_MAPPING = {
    "mineria": ["EXPLOTACIÓN DE MINAS Y CANTERAS"],
    "construccion": ["CONSTRUCCIÓN"],
    "industria": ["INDUSTRIAS MANUFACTURERAS"],
    "tecnologia": ["INFORMACIÓN Y COMUNICACIONES"],
    "salud": ["ACTIVIDADES DE ATENCIÓN DE LA SALUD HUMANA Y DE ASISTENCIA SOCIAL"],
    "comercio": ["COMERCIO AL POR MAYOR Y AL POR MENOR; REPARACIÓN DE VEHÍCULOS AUTOMOTORES Y MOTOCICLETAS"],
    "agricultura": ["AGRICULTURA, GANADERÍA, CAZA, SILVICULTURA Y PESCA"],
    "educacion": ["EDUCACIÓN"],
    "financiero": ["ACTIVIDADES FINANCIERAS Y DE SEGUROS"],
    "transporte": ["TRANSPORTE Y ALMACENAMIENTO"],
    "servicios": [
        "ACTIVIDADES DE SERVICIOS ADMINISTRATIVOS Y DE APOYO",
        "OTRAS ACTIVIDADES DE SERVICIOS",
        "ACTIVIDADES PROFESIONALES, CIENTÍFICAS Y TÉCNICAS",
        "ACTIVIDADES INMOBILIARIAS"
    ],
    "alojamiento": ["ALOJAMIENTO Y SERVICIOS DE COMIDA"]
}

def remove_accents(text):
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def filtrar_candidatos(sector="", descripcion_libre="", clase_riesgo=None, max_resultados=12, min_keyword_length=3):
    catalog = get_catalog()
    sector_norm = sector.lower().strip() if sector else ""
    
    desc_clean = remove_accents(descripcion_libre).lower()
    keywords = [w for w in re.split(r"[\s,;.:()/\\-]+", desc_clean) if len(w) >= min_keyword_length]

    scored = []
    for raw in catalog["codes"]:
        score = 0
        desc_entry = remove_accents(raw["d"]).lower()
        
        sector_str = catalog["sectors"][raw["s"]] if raw["s"] < len(catalog["sectors"]) else ""
        sector_entry = remove_accents(sector_str).lower()
        
        div_str = catalog["divisions"][raw["div"]] if raw["div"] < len(catalog["divisions"]) else ""
        div_entry = remove_accents(div_str).lower()
        
        grupo_str = catalog["grupos"][raw["g"]] if raw["g"] < len(catalog["grupos"]) else ""
        grupo_entry = remove_accents(grupo_str).lower()

        # Coincidencia de clase de riesgo
        if clase_riesgo is not None and raw["r"] == int(clase_riesgo):
            score += 15

        # Coincidencia de sector
        has_sector_match = False
        if sector_norm:
            norm_key = remove_accents(sector_norm)
            mapped_sectors = SECTOR_MAPPING.get(norm_key)
            if mapped_sectors:
                has_sector_match = (sector_str in mapped_sectors)
            else:
                has_sector_match = (sector_norm in sector_entry) or (sector_entry in sector_norm)

        if has_sector_match:
            score += 10

        # Coincidencia de keywords
        for kw in keywords:
            if kw in desc_entry:
                score += 3
            if (kw in div_entry) or (kw in grupo_entry):
                score += 1

        if score > 0:
            scored.append((raw, score))

    # Ordenar de mayor a menor score
    scored.sort(key=lambda x: x[1], reverse=True)
    top_entries = scored[:max_resultados]
    
    return [expand(item[0], catalog) for item in top_entries]

def get_sectores():
    catalog = get_catalog()
    return catalog["sectors"]

def get_codigos_by_sector(sector):
    catalog = get_catalog()
    try:
        idx = catalog["sectors"].index(sector)
    except ValueError:
        return []
    return [expand(e, catalog) for e in catalog["codes"] if e["s"] == idx]

def serializar_para_prompt(entries):
    compacto = []
    for e in entries:
        compacto.append({
            "c": e["codigo_768"],
            "r": e["clase_riesgo"],
            "ciiu": e["ciiu_rev4"],
            "d": e["descripcion"],
            "s": e["sector"],
            "div": e["division"],
            "g": e["grupo"],
        })
    return json.dumps(compacto, ensure_ascii=False)
