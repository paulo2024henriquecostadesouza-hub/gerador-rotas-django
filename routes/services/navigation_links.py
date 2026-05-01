"""
Geração de links de navegação para Google Maps e Waze.
"""
from urllib.parse import quote


def _fmt(lat, lng, decimals=7):
    """Formata coordenadas com ponto decimal fixo."""
    return f"{float(lat):.{decimals}f},{float(lng):.{decimals}f}"


def build_google_maps_link(session, points: list) -> str:
    """
    Gera link do Google Maps com todos os waypoints na ordem otimizada.

    URL montada manualmente para evitar encoding de vírgulas/pipes —
    o Google Maps exige separadores literais (não %2C / %7C).

    Limite prático: ~23 waypoints via URL.
    """
    if not points:
        return ''

    # Origem
    if session.origin_lat and session.origin_lng:
        origin = _fmt(session.origin_lat, session.origin_lng)
        stops = list(points)
    else:
        origin = _fmt(points[0].lat, points[0].lng)
        stops = list(points[1:])

    if not stops:
        return f"https://www.google.com/maps/dir/?api=1&origin={origin}&travelmode=driving"

    destination = _fmt(stops[-1].lat, stops[-1].lng)
    intermediates = stops[:-1]

    url = (
        "https://www.google.com/maps/dir/"
        f"?api=1"
        f"&origin={origin}"
        f"&destination={destination}"
        f"&travelmode=driving"
        f"&dir_action=navigate"   # abre direto em modo de navegação no celular
    )

    if intermediates:
        wps = "|".join(_fmt(p.lat, p.lng) for p in intermediates)
        url += f"&waypoints={wps}"

    return url


def build_waze_stops(session, points: list) -> list:
    """
    Retorna lista de dicts para navegação sequencial no Waze.
    Cada item: { 'label': str, 'url': str }

    O Waze não suporta múltiplos waypoints via URL — a solução prática
    é um botão por parada, para o motorista navegar sequencialmente.
    """
    result = []

    # Ponto de partida (apenas para referência visual — Waze usa GPS do dispositivo)
    if session.origin_lat and session.origin_lng:
        result.append({
            'order': 0,
            'label': session.origin_address or 'Ponto de partida',
            'url': '',          # partida não tem link de navegação
            'is_origin': True,
        })

    for p in points:
        if not p.geocoded or p.lat is None or p.lng is None:
            continue
        coords = _fmt(p.lat, p.lng)
        result.append({
            'order': p.order,
            'label': p.formatted_address or p.address,
            'url': f"https://waze.com/ul?ll={coords}&navigate=yes",
            'is_origin': False,
        })

    return result


# Mantido por compatibilidade (não usado na UI principal)
def build_waze_link(points: list) -> str:
    """Link único Waze para o último ponto da rota."""
    if not points:
        return ''
    last = points[-1]
    coords = _fmt(last.lat, last.lng)
    return f"https://waze.com/ul?ll={coords}&navigate=yes"
