"""
Otimização de rota usando OR-Tools (TSP).
Distâncias calculadas via fórmula de Haversine — sem API externa.
Tempo estimado com velocidade média urbana de 35 km/h.
"""
import math
import logging

from ortools.constraint_solver import routing_enums_pb2, pywrapcp

logger = logging.getLogger(__name__)

VELOCIDADE_MEDIA_KMH = 35.0  # km/h — estimativa urbana


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distância em metros entre dois pontos (fórmula de Haversine)."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _road_distance(lat1, lng1, lat2, lng2) -> float:
    """
    Estima distância viária em metros aplicando fator de tortuosidade (1.35).
    Válido para ambientes urbanos como São Paulo.
    """
    return _haversine(lat1, lng1, lat2, lng2) * 1.35


def _duration_seconds(distance_m: float) -> float:
    """Tempo estimado em segundos para uma distância em metros."""
    km = distance_m / 1000
    horas = km / VELOCIDADE_MEDIA_KMH
    return horas * 3600


def _build_distance_matrix(coords: list) -> list:
    """Monta a matriz NxN de distâncias (metros inteiros) via Haversine."""
    n = len(coords)
    matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = int(_road_distance(
                    coords[i][0], coords[i][1],
                    coords[j][0], coords[j][1],
                ))
    return matrix


def _solve_tsp(distance_matrix: list, start_index: int = 0) -> list:
    """Resolve o TSP com OR-Tools e retorna a lista de índices na ordem otimizada."""
    n = len(distance_matrix)
    manager = pywrapcp.RoutingIndexManager(n, 1, start_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        return distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

    cb_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cb_idx)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = 10

    solution = routing.SolveWithParameters(params)
    if not solution:
        logger.warning("OR-Tools não encontrou solução; retornando ordem original.")
        return list(range(n))

    route, idx = [], routing.Start(0)
    while not routing.IsEnd(idx):
        route.append(manager.IndexToNode(idx))
        idx = solution.Value(routing.NextVar(idx))
    return route


def optimize_route(session, points: list, **kwargs):
    """
    Otimiza a ordem dos pontos da sessão usando OR-Tools + Haversine.
    Atualiza order, distance_to_next_m e duration_to_next_s em cada ponto.
    Atualiza total_distance_m, total_duration_s e is_optimized na sessão.
    """
    logger.info("Otimizando sessão %s com %d pontos.", session.id, len(points))

    has_origin = bool(session.origin_lat and session.origin_lng)

    # Monta lista de coordenadas: [origem opcional] + pontos
    coords = []
    if has_origin:
        coords.append((session.origin_lat, session.origin_lng))
    for p in points:
        coords.append((p.lat, p.lng))

    matrix = _build_distance_matrix(coords)
    optimized_order = _solve_tsp(matrix, start_index=0)

    # Mapeia índices de volta para objetos RoutePoint
    offset = 1 if has_origin else 0
    ordered_points = []
    for idx in optimized_order:
        if has_origin and idx == 0:
            continue  # pula a origem
        point_idx = idx - offset
        if 0 <= point_idx < len(points):
            ordered_points.append(points[point_idx])

    # Calcula distância e tempo de cada trecho consecutivo
    leg_coords = []
    if has_origin:
        leg_coords.append((session.origin_lat, session.origin_lng))
    for p in ordered_points:
        leg_coords.append((p.lat, p.lng))

    leg_distances, leg_durations = [], []
    for i in range(len(leg_coords) - 1):
        lat1, lng1 = leg_coords[i]
        lat2, lng2 = leg_coords[i + 1]
        dist = _road_distance(lat1, lng1, lat2, lng2)
        dur  = _duration_seconds(dist)
        leg_distances.append(dist)
        leg_durations.append(dur)

    # Persiste nova ordem e métricas por trecho
    for new_order, point in enumerate(ordered_points, start=1):
        trecho_idx = new_order - 1
        dist = leg_distances[trecho_idx] if trecho_idx < len(leg_distances) else None
        dur  = leg_durations[trecho_idx] if trecho_idx < len(leg_durations) else None
        point.order = new_order
        point.distance_to_next_m = dist
        point.duration_to_next_s = dur
        point.save(update_fields=['order', 'distance_to_next_m', 'duration_to_next_s'])

    total_dist = sum(leg_distances)
    total_dur  = sum(leg_durations)

    session.total_distance_m = total_dist if total_dist > 0 else None
    session.total_duration_s = total_dur  if total_dur  > 0 else None
    session.is_optimized = True
    session.save(update_fields=['total_distance_m', 'total_duration_s', 'is_optimized'])

    logger.info("Otimização concluída: %.1f km, %.0f min.", total_dist / 1000, total_dur / 60)
    return session
