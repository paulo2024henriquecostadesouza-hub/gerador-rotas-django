import uuid
from django.db import models


class RouteSession(models.Model):
    """Sessão de rota criada pelo operador."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    origin_address = models.TextField(blank=True, help_text="Endereço de partida/origem")
    origin_lat = models.FloatField(null=True, blank=True)
    origin_lng = models.FloatField(null=True, blank=True)

    fuel_consumption = models.FloatField(
        default=10.0, help_text="Consumo médio em km/l"
    )
    fuel_price = models.FloatField(
        default=6.50, help_text="Preço do litro de combustível em R$"
    )

    # Resultado do cálculo
    total_distance_m = models.FloatField(null=True, blank=True, help_text="Distância total em metros")
    total_duration_s = models.FloatField(null=True, blank=True, help_text="Tempo estimado em segundos")
    is_optimized = models.BooleanField(default=False)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sessão de Rota'
        verbose_name_plural = 'Sessões de Rota'

    def __str__(self):
        return f"Rota {str(self.id)[:8]} — {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    @property
    def total_distance_km(self):
        if self.total_distance_m:
            return round(self.total_distance_m / 1000, 2)
        return None

    @property
    def total_duration_min(self):
        if self.total_duration_s:
            return round(self.total_duration_s / 60, 1)
        return None

    @property
    def fuel_liters(self):
        if self.total_distance_km and self.fuel_consumption:
            return round(self.total_distance_km / self.fuel_consumption, 2)
        return None

    @property
    def fuel_cost(self):
        if self.fuel_liters and self.fuel_price:
            return round(self.fuel_liters * self.fuel_price, 2)
        return None


class RoutePoint(models.Model):
    """Ponto individual de uma rota."""

    session = models.ForeignKey(
        RouteSession, on_delete=models.CASCADE, related_name='points'
    )
    order = models.PositiveIntegerField(help_text="Ordem na rota otimizada")
    address = models.TextField(help_text="Endereço original informado")
    formatted_address = models.TextField(blank=True, help_text="Endereço formatado pela API")
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    geocoded = models.BooleanField(default=False)
    geocode_error = models.TextField(blank=True)

    # Distância e tempo até o próximo ponto
    distance_to_next_m = models.FloatField(null=True, blank=True)
    duration_to_next_s = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Ponto da Rota'
        verbose_name_plural = 'Pontos da Rota'

    def __str__(self):
        return f"#{self.order} — {self.address[:50]}"

    @property
    def distance_to_next_km(self):
        if self.distance_to_next_m:
            return round(self.distance_to_next_m / 1000, 2)
        return None

    @property
    def duration_to_next_min(self):
        if self.duration_to_next_s:
            return round(self.duration_to_next_s / 60, 1)
        return None
