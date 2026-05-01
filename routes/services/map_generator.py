"""
Geração do mapa interativo usando Folium.
Retorna HTML completo para ser exibido em um <iframe>.
"""
import folium


# Paleta de cores: azul escuro → laranja → vermelho (combinando com o tema CCO)
_COLORS = [
    '#1a73e8', '#1967d2', '#185abc',
    '#C16A42', '#b05c35', '#9e4e28',
    '#d93025', '#c5221f',
]


def _marker_color(index: int, total: int) -> str:
    if total <= 1:
        return _COLORS[0]
    ratio = index / max(total - 1, 1)
    return _COLORS[int(ratio * (len(_COLORS) - 1))]


def _numbered_icon(number: int, color: str) -> folium.DivIcon:
    return folium.DivIcon(
        html=f"""
        <div style="
            background:{color};
            color:#fff;
            border-radius:50%;
            width:28px;height:28px;
            display:flex;align-items:center;justify-content:center;
            font-size:12px;font-weight:700;
            font-family:'Rubik',Arial,sans-serif;
            border:2px solid rgba(255,255,255,.85);
            box-shadow:0 2px 8px rgba(0,0,0,.5);
            margin-left:-14px;margin-top:-14px;
        ">{number}</div>
        """,
        icon_size=(28, 28),
        icon_anchor=(14, 14),
    )


def generate_route_map(session, points: list) -> str:
    """
    Gera mapa Folium com os pontos numerados e linha da rota.
    Retorna HTML completo (string) para embed em iframe.
    """
    if not points:
        return _empty_map_html()

    center_lat = sum(p.lat for p in points) / len(points)
    center_lng = sum(p.lng for p in points) / len(points)

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles='OpenStreetMap',
    )

    # Estilo escuro inspirado no tema do CCO
    m.get_root().html.add_child(folium.Element("""
    <style>
      body { background: #1a2e28; margin: 0; }
      .leaflet-container { background: #1a2e28; }
    </style>
    """))

    total = len(points)

    # Marcador de origem
    if session.origin_lat and session.origin_lng:
        folium.Marker(
            location=[session.origin_lat, session.origin_lng],
            popup=folium.Popup(
                f'<div style="font-family:Arial;min-width:160px">'
                f'<b style="color:#2E4E46">PARTIDA</b><br>'
                f'{session.origin_address or "Origem"}'
                f'</div>',
                max_width=260,
            ),
            icon=folium.Icon(color='green', icon='home', prefix='fa'),
            tooltip='Ponto de Partida',
        ).add_to(m)

    # Linha tracejada da rota
    route_coords = []
    if session.origin_lat and session.origin_lng:
        route_coords.append([session.origin_lat, session.origin_lng])
    for p in points:
        route_coords.append([p.lat, p.lng])

    if len(route_coords) >= 2:
        folium.PolyLine(
            locations=route_coords,
            color='#C16A42',
            weight=3,
            opacity=0.75,
            dash_array='8 4',
        ).add_to(m)

    # Marcadores numerados
    for idx, point in enumerate(points):
        color = _marker_color(idx, total)
        order = point.order

        addr = point.formatted_address or point.address
        dist_str = ''
        if point.distance_to_next_km:
            dist_str = f'<br><small>Próximo: <b>{point.distance_to_next_km} km</b>'
            if point.duration_to_next_min:
                dist_str += f' / {point.duration_to_next_min:.0f} min'
            dist_str += '</small>'

        is_last = (idx == total - 1)
        popup_html = (
            f'<div style="font-family:Arial;min-width:180px">'
            f'<div style="background:{color};color:#fff;padding:5px 10px;border-radius:4px;margin-bottom:6px">'
            f'<b>Ponto #{order}</b></div>'
            f'<div style="font-size:13px;padding:2px 0">{addr}</div>'
            f'{dist_str}'
            f'{"<br><i style=\'color:#888\'>Destino final</i>" if is_last else ""}'
            f'</div>'
        )

        folium.Marker(
            location=[point.lat, point.lng],
            popup=folium.Popup(popup_html, max_width=280),
            icon=_numbered_icon(order, color),
            tooltip=f'#{order} — {addr[:45]}',
        ).add_to(m)

    return m.get_root().render()


def _empty_map_html() -> str:
    return (
        '<!DOCTYPE html><html><body style="'
        'background:#1a2e28;color:#a8c4bc;font-family:Rubik,sans-serif;'
        'display:flex;align-items:center;justify-content:center;height:100vh;margin:0">'
        '<p>Nenhum ponto geocodificado para exibir.</p></body></html>'
    )
