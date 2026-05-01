from django.urls import path
from . import views

app_name = 'routes'

urlpatterns = [
    # Página inicial — formulário de nova rota
    path('', views.IndexView.as_view(), name='index'),

    # Criar rota (POST do formulário)
    path('criar/', views.IndexView.as_view(), name='create'),

    # Histórico de rotas
    path('historico/', views.SessionsListView.as_view(), name='sessions'),

    # Detalhe de uma sessão
    path('rota/<uuid:session_id>/', views.SessionDetailView.as_view(), name='session_detail'),

    # Otimizar rota (AJAX POST)
    path('rota/<uuid:session_id>/otimizar/', views.OptimizeView.as_view(), name='optimize'),

    # API GeoJSON das regionais para o mapa Leaflet
    path('api/regioes/', views.RegioesView.as_view(), name='regioes'),

    # Exportar PDF
    path('rota/<uuid:session_id>/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),

    # Modo navegação sequencial (mobile)
    path('rota/<uuid:session_id>/navegar/', views.NavigationModeView.as_view(), name='navigate'),
]
