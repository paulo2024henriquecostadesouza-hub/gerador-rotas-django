# Gerador de Rotas — Fiscais CPLU

Sistema web em **Django** para gerar rotas otimizadas para fiscais de campo. Recebe uma lista de endereços, geocodifica automaticamente via OpenStreetMap (Nominatim), aplica otimização por proximidade (OR-Tools) e exibe um mapa interativo com a sequência sugerida de visitas.

## Funcionalidades

- Upload de lista de endereços ou digitação manual
- **Geocodificação automática** via Nominatim (OpenStreetMap — gratuito)
- **Otimização de rota** por menor distância (OR-Tools / TSP)
- **Mapa interativo** com Leaflet.js — pontos numerados e sequência visual
- **Links de navegação** gerados automaticamente (Google Maps / Waze)
- **Exportação PDF** da rota com ReportLab
- Histórico de sessões salvo no banco
- Estimativa de distância total e custo de combustível

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Python 3 / Django 4.2 | Framework web |
| Leaflet.js | Mapa interativo |
| OR-Tools (Google) | Otimização de rota (TSP) |
| geopy / Nominatim | Geocodificação gratuita |
| folium | Geração do HTML do mapa |
| ReportLab + Pillow | Exportação PDF |
| SQLite | Banco de dados local |
| python-decouple | Variáveis de ambiente |

## Instalação

```bash
# 1. Clonar o repositório
git clone https://github.com/paulo2024henriquecostadesouza-hub/gerador-rotas-django.git
cd gerador-rotas-django

# 2. Instalar dependências (ou usar instalar.bat no Windows)
pip install -r requirements.txt

# 3. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com sua SECRET_KEY

# 4. Aplicar migrações e iniciar
python manage.py migrate
python manage.py runserver 8508
```

> No Windows, execute `instalar.bat` e depois `iniciar_8508.bat`.

## Estrutura

```
gerador-rotas-django/
├── config/           ← Configurações Django (settings, urls, wsgi)
├── routes/
│   ├── models.py     ← Modelos: Sessão, Endereço, Rota
│   ├── views.py      ← Views principais
│   ├── urls.py
│   ├── services/
│   │   ├── geocoding.py       ← Geocodificação Nominatim
│   │   ├── optimization.py    ← Algoritmo TSP (OR-Tools)
│   │   ├── map_generator.py   ← Geração do mapa Leaflet
│   │   ├── navigation_links.py← Links Google Maps / Waze
│   │   └── pdf_export.py      ← Exportação PDF (ReportLab)
│   ├── templates/routes/      ← Templates HTML
│   └── static/routes/        ← CSS e dados regionais
├── requirements.txt
├── manage.py
└── .env.example
```

## Desenvolvido por

Paulo Henrique — Analista CCO / CPLU
