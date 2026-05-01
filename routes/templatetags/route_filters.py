from django import template

register = template.Library()


@register.filter
def duration_fmt(minutes):
    """Converte minutos float em string '1h 23min' ou '45 min'."""
    if not minutes:
        return '—'
    total = int(float(minutes))
    h = total // 60
    m = total % 60
    if h > 0:
        return f'{h}h {m}min'
    return f'{m} min'
