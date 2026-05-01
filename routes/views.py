import json
import logging
import os

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import RouteSession, RoutePoint
from .services.geocoding import geocode_addresses, _parse_input as parse_origin_input
from .services.navigation_links import build_google_maps_link, build_waze_link, build_waze_stops
from .services.optimization import optimize_route
from .services.pdf_export import generate_route_pdf

logger = logging.getLogger(__name__)


def _base_context(request):
    return {
        'default_consumption': settings.FUEL_CONSUMPTION_KM_L,
        'default_fuel_price': settings.FUEL_PRICE_PER_LITER,
    }


class IndexView(View):
    """GET / — formulário | POST / — geocodifica e redireciona."""

    def get(self, request):
        ctx = _base_context(request)
        ctx['form_data'] = {}
        return render(request, 'routes/index.html', ctx)

    def post(self, request):
        ctx = _base_context(request)

        raw = request.POST.get('addresses', '').strip()
        fuel_consumption = float(request.POST.get('fuel_consumption') or settings.FUEL_CONSUMPTION_KM_L)
        fuel_price = float(request.POST.get('fuel_price') or settings.FUEL_PRICE_PER_LITER)

        addresses = [a.strip() for a in raw.splitlines() if a.strip()]

        if not addresses:
            messages.error(request, 'Insira pelo menos um endereço.')
            ctx['form_data'] = request.POST
            return render(request, 'routes/index.html', ctx)

        if len(addresses) > 25:
            messages.error(request, 'Máximo de 25 endereços por vez.')
            ctx['form_data'] = request.POST
            return render(request, 'routes/index.html', ctx)

        # ── Ponto de partida — três modos: gps / address / coords ──────────
        origin_mode = request.POST.get('origin_mode', 'gps')
        origin_lat = None
        origin_lng = None
        origin_address = ''

        if origin_mode == 'gps':
            try:
                origin_lat = float(request.POST.get('origin_lat') or '')
                origin_lng = float(request.POST.get('origin_lng') or '')
                origin_address = 'Localização atual (GPS)'
            except (ValueError, TypeError):
                pass

        elif origin_mode == 'address':
            origin_address_text = request.POST.get('origin_address_text', '').strip()
            if origin_address_text:
                # Tenta extrair coords embutidas (formato "Endereço\tLAT,LNG")
                addr_text, parsed_lat, parsed_lng = parse_origin_input(origin_address_text)
                if parsed_lat is not None and parsed_lng is not None:
                    origin_lat = parsed_lat
                    origin_lng = parsed_lng
                    origin_address = addr_text or origin_address_text
                else:
                    # Geocodifica pelo texto
                    geocoded_origin = geocode_addresses([origin_address_text])
                    if geocoded_origin and geocoded_origin[0].get('geocoded'):
                        origin_lat = geocoded_origin[0]['lat']
                        origin_lng = geocoded_origin[0]['lng']
                        origin_address = geocoded_origin[0].get('formatted_address') or origin_address_text
                    else:
                        messages.warning(request, f'Não foi possível geocodificar o ponto de partida: "{origin_address_text}". A rota será gerada sem partida fixa.')
                        origin_address = origin_address_text

        elif origin_mode == 'coords':
            try:
                origin_lat = float(request.POST.get('origin_coord_lat') or '')
                origin_lng = float(request.POST.get('origin_coord_lng') or '')
                origin_address = f'Coordenadas: {origin_lat:.6f}, {origin_lng:.6f}'
            except (ValueError, TypeError):
                messages.warning(request, 'Coordenadas de partida inválidas. A rota será gerada sem partida fixa.')

        session = RouteSession.objects.create(
            origin_address=origin_address,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            fuel_consumption=fuel_consumption,
            fuel_price=fuel_price,
        )

        # Geocodificar endereços
        geocoded = geocode_addresses(addresses)
        for idx, item in enumerate(geocoded):
            RoutePoint.objects.create(
                session=session,
                order=idx + 1,
                address=item['address'],
                formatted_address=item.get('formatted_address', ''),
                lat=item.get('lat'),
                lng=item.get('lng'),
                geocoded=item.get('geocoded', False),
                geocode_error=item.get('error', ''),
            )

        ok_count = sum(1 for g in geocoded if g.get('geocoded'))
        messages.success(request, f'{ok_count} de {len(addresses)} endereços geocodificados com sucesso.')
        return redirect('routes:session_detail', session_id=session.id)


class SessionDetailView(View):
    """GET /rota/<id>/ — detalhe da rota."""

    def get(self, request, session_id):
        session = get_object_or_404(RouteSession, pk=session_id)
        points = list(session.points.order_by('order'))
        geocoded_points = [p for p in points if p.geocoded]
        error_points = [p for p in points if not p.geocoded]

        google_maps_link = build_google_maps_link(session, geocoded_points) if geocoded_points else ''
        waze_link = build_waze_link(geocoded_points) if geocoded_points else ''
        waze_stops_list = build_waze_stops(session, geocoded_points) if geocoded_points else []

        # Pontos como JSON para o mapa Leaflet
        points_json = json.dumps([
            {
                'order': p.order,
                'lat': float(p.lat),
                'lng': float(p.lng),
                'label': p.formatted_address or p.address,
            }
            for p in geocoded_points
        ])

        # Origem (GPS) como JSON se disponível
        origin_json = 'null'
        if session.origin_lat and session.origin_lng:
            origin_json = json.dumps({
                'lat': float(session.origin_lat),
                'lng': float(session.origin_lng),
                'label': session.origin_address or 'Ponto de partida',
            })

        ctx = _base_context(request)
        ctx.update({
            'session': session,
            'points': points,
            'geocoded_points': geocoded_points,
            'error_points': error_points,
            'points_count': len(geocoded_points),
            'google_maps_link': google_maps_link,
            'waze_link': waze_link,
            'waze_stops': waze_stops_list,
            'points_json': points_json,
            'origin_json': origin_json,
        })
        return render(request, 'routes/session.html', ctx)


class OptimizeView(View):
    """POST /rota/<id>/otimizar/ — AJAX, retorna JSON."""

    def post(self, request, session_id):
        session = get_object_or_404(RouteSession, pk=session_id)
        points = list(session.points.filter(geocoded=True))

        if len(points) < 2:
            return JsonResponse({'ok': False, 'error': 'São necessários pelo menos 2 pontos geocodificados.'}, status=400)

        try:
            optimize_route(session, points)
            return JsonResponse({'ok': True})
        except Exception as exc:
            logger.exception('Erro ao otimizar rota %s', session_id)
            return JsonResponse({'ok': False, 'error': str(exc)}, status=500)


class RegioesView(View):
    """GET /api/regioes/ — GeoJSON das regionais para o mapa Leaflet."""

    def get(self, request):
        geojson_path = os.path.join(settings.BASE_DIR, 'routes', 'static', 'routes', 'data', 'regioes.json')
        try:
            with open(geojson_path, encoding='utf-8') as f:
                data = json.load(f)
            return JsonResponse(data, safe=False)
        except FileNotFoundError:
            return JsonResponse({'type': 'FeatureCollection', 'features': []}, status=200)


class SessionsListView(View):
    """GET /historico/ — lista as últimas sessões."""

    def get(self, request):
        sessions = RouteSession.objects.prefetch_related('points').order_by('-created_at')[:30]
        ctx = _base_context(request)
        ctx['sessions'] = sessions
        return render(request, 'routes/sessions.html', ctx)


class ExportPDFView(View):
    """GET /rota/<id>/pdf/ — gera e devolve PDF."""

    def get(self, request, session_id):
        session = get_object_or_404(RouteSession, pk=session_id)
        points = list(session.points.order_by('order'))

        try:
            pdf_bytes = generate_route_pdf(session, points)
        except Exception as exc:
            logger.exception('Erro ao gerar PDF %s', session_id)
            return HttpResponse(f'Erro: {exc}', status=500, content_type='text/plain')

        short_id = str(session.id)[:8]
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rota_{short_id}.pdf"'
        return response


class NavigationModeView(View):
    """GET /rota/<id>/navegar/ — modo navegação sequencial para celular."""

    def get(self, request, session_id):
        session = get_object_or_404(RouteSession, pk=session_id)
        geocoded_points = list(session.points.filter(geocoded=True).order_by('order'))

        # Monta lista de paradas incluindo ponto de partida
        stops = []
        if session.origin_lat and session.origin_lng:
            stops.append({
                'index': 0,
                'order': 0,
                'is_origin': True,
                'label': session.origin_address or 'Ponto de partida',
                'lat': float(session.origin_lat),
                'lng': float(session.origin_lng),
                'waze_url': '',
                'maps_url': '',
            })

        for p in geocoded_points:
            lat, lng = float(p.lat), float(p.lng)
            coord = f"{lat:.7f},{lng:.7f}"
            stops.append({
                'index': len(stops),
                'order': p.order,
                'is_origin': False,
                'label': p.formatted_address or p.address,
                'lat': lat,
                'lng': lng,
                'waze_url': f"https://waze.com/ul?ll={coord}&navigate=yes",
                'maps_url': (
                    f"https://www.google.com/maps/dir/?api=1"
                    f"&destination={coord}&travelmode=driving&dir_action=navigate"
                ),
            })

        ctx = {
            'session': session,
            'stops_json': json.dumps(stops),
            'total': len(stops),
            'has_origin': bool(session.origin_lat and session.origin_lng),
        }
        return render(request, 'routes/navigate.html', ctx)
