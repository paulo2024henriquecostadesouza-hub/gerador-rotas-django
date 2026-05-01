from django.contrib import admin
from .models import RouteSession, RoutePoint


class RoutePointInline(admin.TabularInline):
    model = RoutePoint
    extra = 0
    readonly_fields = ['geocoded', 'geocode_error', 'formatted_address', 'lat', 'lng',
                       'distance_to_next_m', 'duration_to_next_s']
    fields = ['order', 'address', 'formatted_address', 'lat', 'lng',
              'geocoded', 'geocode_error', 'distance_to_next_m', 'duration_to_next_s']


@admin.register(RouteSession)
class RouteSessionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'created_at', 'origin_address', 'total_distance_km',
                    'total_duration_min', 'fuel_cost', 'is_optimized']
    list_filter = ['is_optimized', 'created_at']
    search_fields = ['origin_address', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_distance_km',
                       'total_duration_min', 'fuel_liters', 'fuel_cost']
    inlines = [RoutePointInline]

    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'


@admin.register(RoutePoint)
class RoutePointAdmin(admin.ModelAdmin):
    list_display = ['session', 'order', 'address', 'geocoded', 'lat', 'lng']
    list_filter = ['geocoded', 'session']
    search_fields = ['address', 'formatted_address']
    readonly_fields = ['distance_to_next_km', 'duration_to_next_min']
