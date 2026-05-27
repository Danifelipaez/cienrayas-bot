# Graph Report - .  (2026-05-27)

## Corpus Check
- Corpus is ~12,069 words - fits in a single context window. You may not need a graph.

## Summary
- 193 nodes · 347 edges · 14 communities (13 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.7)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `full_ranking()` - 12 edges
2. `build_fishing_prompt()` - 11 edges
3. `_zone_ipp()` - 11 edges
4. `evaluate()` - 10 edges
5. `_handle_fishing_query()` - 10 edges
6. `get_weather()` - 10 edges
7. `get_satellite_data()` - 9 edges
8. `get_water_quality()` - 9 edges
9. `local_wind_name()` - 8 edges
10. `str` - 8 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `evaluate()`  [EXTRACTED]
  test_bot.py → core/semaphore.py
- `main()` --calls--> `generate_fishing_response()`  [EXTRACTED]
  test_bot.py → services/llm.py
- `main()` --calls--> `full_ranking()`  [EXTRACTED]
  test_data.py → core/zone_analysis.py
- `main()` --calls--> `evaluate()`  [EXTRACTED]
  test_data.py → core/semaphore.py
- `main()` --calls--> `generate_map()`  [EXTRACTED]
  test_data.py → services/map_generator.py

## Hyperedges (group relationships)
- **Real-Time Data Collection Pipeline** — weather_py, satellite_py, water_quality_py, webhook_py [INFERRED]
- **Safety Evaluation Flow** — semaphore_py, weather_data, water_quality_data, semaphore_signal [INFERRED]
- **Fishing Zone Recommendation** — zone_analysis_py, satellite_data, water_quality_data, ipp_index, fishing_zones [INFERRED]
- **AI Response Generation with Caching** — llm_py, prompts_py, groq_api, llm_cache [INFERRED]
- **Fisher Conversation Interaction Loop** — fisher_user, webhook_py, conversation_state, feedback_loop, meta_whatsapp_api [INFERRED]

## Communities (14 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.00
Nodes (43): Cienaga Grande de Santa Marta, CienRayas Bot, Configuration Module, Conversation State Manager, Core Business Logic, FastAPI Application, Fisher Feedback Loop, Fish Species (+35 more)

### Community 1 - "Community 1"
Cohesion: 0.00
Nodes (26): BackgroundTasks, get_state(), is_awaiting_feedback(), is_duplicate(), looks_like_feedback(), looks_like_new_query(), _purge_old_ids(), bool (+18 more)

### Community 2 - "Community 2"
Cohesion: 0.00
Nodes (21): main(), Simulador completo del bot — sin WhatsApp ni ngrok. Muestra exactamente el mens, main(), Prueba rápida de todas las fuentes de datos y el análisis de zonas. NO necesita, Devuelve la zona con el IPP más alto., recommend_zone(), _erddap_average(), get_chlorophyll() (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.00
Nodes (21): get_fishing_context(), get_lunar_phase(), interpret_water_color(), local_wind_name(), bool, float, str, Conocimiento técnico y empírico de la Ciénaga Grande de Santa Marta. Fuente téc (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.00
Nodes (17): lifespan(), ping(), UptimeRobot llama aquí cada 10 min para evitar que Render duerma el servicio., FastAPI, int, daily_refresh_loop(), _fetch_from_ideam(), str (+9 more)

### Community 5 - "Community 5"
Cohesion: 0.00
Nodes (17): float, Análisis multivariable para determinar la zona de mayor probabilidad de pesca e, Temperatura superficial: óptimo 26–30 °C → 100., Clorofila: >4 mg/m³ es buena mancha; <0.5 agua pobre., Turbidez: baja (<30 NTU) es mejor para boliche; muy alta perjudica redes., pH: rango ideal estuarino 7.0–8.5., Puntaje de salinidad: cuánto se acerca la salinidad actual al rango     óptimo, Índice de Potencial Pesquero (IPP) de 0 a 100 para una zona. (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.00
Nodes (17): _basemap_or_fallback(), _cache_hit(), generar_mapa(), generate_map(), _ipp_color(), _north_arrow(), _north_arrow_v2(), float (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.00
Nodes (6): Semaphore, _call_groq(), generate_feedback_ack(), generate_fishing_response(), _get_semaphore(), str

### Community 8 - "Community 8"
Cohesion: 0.00
Nodes (4): str, send(), send_image(), send_text()

## Knowledge Gaps
- **6 isolated node(s):** `bool`, `float`, `BackgroundTasks`, `Request`, `Semaphore` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.