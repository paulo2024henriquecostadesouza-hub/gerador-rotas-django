"""
Geocodificação gratuita usando Nominatim (OpenStreetMap).
Sem necessidade de chave de API.

Formatos suportados por linha:
  - "Rua X, 100, SP\t-23.6066,-46.5928"   → usa as coords diretamente
  - "-23.6066,-46.5928"                     → usa as coords, sem endereço
  - "Rua X, 100, SP"                        → geocodifica via Nominatim
"""
import logging
import re
import time

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)

_geocoder = Nominatim(user_agent="cco_gerador_rotas/1.0", timeout=10)

# Regex para detectar par de coordenadas decimais
_RE_COORDS = re.compile(r'(-?\d{1,3}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)')


def _parse_input(raw: str):
    """
    Extrai (endereço_texto, lat, lng) de uma string de entrada.

    Formatos reconhecidos:
      - "Endereço\tLAT,LNG"    → (endereço, lat, lng)
      - "LAT,LNG"               → ('', lat, lng)
      - "Endereço"              → (endereço, None, None)
    """
    raw = raw.strip()

    # Formato com tabulação: "Endereço<TAB>-23.xxx,-46.xxx"
    if '\t' in raw:
        addr_part, coord_part = raw.split('\t', 1)
        m = _RE_COORDS.search(coord_part.strip())
        if m:
            return addr_part.strip(), float(m.group(1)), float(m.group(2))
        return addr_part.strip(), None, None

    # Somente coordenadas: "-23.xxx,-46.xxx"
    m = _RE_COORDS.fullmatch(raw)
    if m:
        return '', float(m.group(1)), float(m.group(2))

    return raw, None, None


def geocode_addresses(addresses: list, **kwargs) -> list:
    """
    Processa uma lista de entradas (endereço, coords ou combinação).
    Retorna lista de dicts com: address, formatted_address, lat, lng, geocoded, error.
    """
    results = []
    nominatim_calls = 0

    for raw in addresses:
        if not raw or not raw.strip():
            continue

        address_text, lat, lng = _parse_input(raw.strip())

        # ── Coordenadas já disponíveis — pula Nominatim ──────────────────
        if lat is not None and lng is not None:
            results.append({
                'address': raw.strip(),
                'formatted_address': address_text if address_text else f'{lat:.6f}, {lng:.6f}',
                'lat': lat,
                'lng': lng,
                'geocoded': True,
                'error': '',
            })
            continue

        # ── Sem texto para geocodificar ───────────────────────────────────
        if not address_text:
            results.append({
                'address': raw.strip(),
                'formatted_address': '',
                'lat': None, 'lng': None,
                'geocoded': False,
                'error': 'Endereço vazio.',
            })
            continue

        # ── Geocodificação via Nominatim ──────────────────────────────────
        if nominatim_calls > 0:
            time.sleep(1.1)
        nominatim_calls += 1

        try:
            location = _geocoder.geocode(address_text, language='pt')

            if location:
                results.append({
                    'address': raw.strip(),
                    'formatted_address': location.address,
                    'lat': location.latitude,
                    'lng': location.longitude,
                    'geocoded': True,
                    'error': '',
                })
            else:
                # Fallback: remove número e tenta de novo
                simplified = _simplify_address(address_text)
                if simplified != address_text:
                    time.sleep(1.1)
                    nominatim_calls += 1
                    location2 = _geocoder.geocode(simplified, language='pt')
                    if location2:
                        results.append({
                            'address': raw.strip(),
                            'formatted_address': location2.address,
                            'lat': location2.latitude,
                            'lng': location2.longitude,
                            'geocoded': True,
                            'error': '',
                        })
                        continue

                logger.warning("Endereço não encontrado: %s", address_text)
                results.append({
                    'address': raw.strip(),
                    'formatted_address': '',
                    'lat': None, 'lng': None,
                    'geocoded': False,
                    'error': 'Endereço não encontrado pelo Nominatim.',
                })

        except GeocoderTimedOut:
            logger.error("Timeout ao geocodificar: %s", address_text)
            results.append({
                'address': raw.strip(),
                'formatted_address': '',
                'lat': None, 'lng': None,
                'geocoded': False,
                'error': 'Timeout — tente novamente.',
            })
        except GeocoderServiceError as exc:
            logger.error("Erro de serviço ao geocodificar '%s': %s", address_text, exc)
            results.append({
                'address': raw.strip(),
                'formatted_address': '',
                'lat': None, 'lng': None,
                'geocoded': False,
                'error': str(exc),
            })

    return results


def _simplify_address(address: str) -> str:
    """Remove número do endereço para tentar geocodificação mais ampla."""
    parts = address.split(',')
    if len(parts) > 2:
        return ', '.join(parts[1:]).strip()
    return address
