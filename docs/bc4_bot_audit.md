# Auditoría del Bot BC4

## 0. Resumen ejecutivo
El repositorio BC4 implementa un ecosistema completo para un bot de análisis técnico y generación de señales sobre criptomonedas (BTC, ETH, SOL). Consta de un backend en Python que ingiere datos de Binance, calcula indicadores avanzados, detecta setups y expone una API REST, y de un frontend en Next.js que visualiza contexto de mercado y señales en tiempo real. El pipeline principal descarga velas OHLCV, persiste la información en SQLite y ejecuta un motor de señales basado en estructura de mercado, indicadores (EMA, ATR, ADX, RSI, VWAP) y un filtro maestro de BTC.

## 1. Tipo de bot y propósito
- **Clasificación**: Bot de análisis cuantitativo/TA con capacidades de escaneo discrecional guiado por reglas.
- **Objetivo principal**: Evaluar múltiples activos (BTC/USDT, ETH/USDT, SOL/USDT) en distintos marcos temporales (1h, 4h) para detectar oportunidades LONG/SHORT alineadas con el contexto de BTC.
- **Flujo de trabajo**: ingestión de datos → cálculo de indicadores → evaluación de contexto BTC → detección de setups → scoring y filtrado → exposición vía API y dashboard web.

## 2. Stack tecnológico
- **Backend** (carpeta `backend/`):
  - Python 3.10+, FastAPI 0.104, Uvicorn, Pydantic v2 para esquemas.
  - ccxt para conexión con Binance, pandas/numpy para manipulación de datos.
  - SQLAlchemy 2.x y SQLite (archivo `crypto_data.db`) como almacenamiento.
  - python-dotenv para gestión de configuración.
- **Frontend** (carpeta `frontend/`):
  - Next.js 14 con App Router, React 18, TypeScript.
  - SWR para data fetching, TailwindCSS/Lucide para UI.
  - lightweight-charts para renderizar velas + indicadores.
- **Utilidades**: scripts CLI (`main.py`, `run_scanner.py`, `update_cvd_data.py`) y tooling de tests con pytest.

## 3. Arquitectura y estructura
- **Organización general**: dos paquetes independientes (`backend/`, `frontend/`) con configuración y dependencias aisladas.
- **Backend**:
  - `src/config`: carga de variables (.env) y parámetros globales.
  - `src/data`: cliente de exchange, fetcher coordinado, persistencia OHLCV, cálculo/almacenamiento de CVD.
  - `src/indicators`: librería propia de indicadores técnicos y estructura de mercado.
  - `src/signals`: motor completo (filtro BTC, detectores de patrones, scorer, entidad `Signal`).
  - `src/api`: FastAPI + routers (`/api/health`, `/api/market`, `/api/signals`) y esquemas de respuesta.
  - `tests/`: suite PyTest que cubre fetcher, indicadores, motor de señales y patrones.
- **Frontend**:
  - `app/page.tsx`: home que coordina llamadas y renderiza dashboard.
  - `components/`: módulos para charts, overview de mercado, panel de señales, layout general.
  - `lib/api`: cliente REST configurable por `NEXT_PUBLIC_API_URL`, hooks SWR y tipado compartido.

## 4. Funcionalidades actuales
- **Ingesta y almacenamiento**:
  - `main.py` descarga velas recientes para símbolos/timeframes configurados, valida integridad y persiste en SQLite (`ohlcv`).
  - `DataStorage` implementa upsert con restricción única y acceso para consultas históricas.
  - `update_cvd_data.py` calcula y guarda CVD por vela en tabla `cvd_data`.
- **Cálculo de indicadores y estructura**:
  - EMA (20, 50), ATR, ADX, RSI, VWAP, VWAP por sesión.
  - Detección de swings y agrupación de soportes/resistencias con tolerancia configurable.
- **Motor de señales** (`SignalEngine`):
  - Filtro maestro BTC (contexto tendencia, fuerza, volatilidad, sesión) vía `BTCFilter`.
  - Detector de setups long/short apoyado en estructura de mercado e indicadores multi-timeframe.
  - Puntaje final y nivel de confianza mediante `SignalScorer`; genera niveles (SL/TP) basados en ATR.
  - Salida priorizada (máx. dos señales ordenadas por score) con metadatos y razones.
- **API REST**:
  - `/api/market/overview`: resumen de activos, contexto BTC, métricas de tendencia.
  - `/api/market/chart/{symbol}/{timeframe}`: velas, indicadores, estructura, niveles y CVD alineado.
  - `/api/signals/current`: ejecuta `SignalEngine` bajo demanda y devuelve señales vigentes.
  - `/api/health/ping`: verificación básica.
- **Dashboard web**:
  - Overview con cards por activo (tendencias 4h/1h, cambios 24h, ADX/RSI/ATR/EMAs).
  - Banner de contexto BTC y estado del filtro maestro.
  - Panel de señales en tiempo real (actualiza cada 60s).
  - Chart interactivo estilo TradingView con velas, EMAs, VWAP y líneas de soporte/resistencia + CVD.

## 5. Configuración y dependencias
- **Variables de entorno backend** (`backend/.env.example`):
  - `EXCHANGE` (por defecto binance), `SYMBOLS`, `TIMEFRAMES`, `DEFAULT_LIMIT` (candles a obtener), `DB_PATH` (ruta SQLite).
- **Dependencias backend**: definidas en `requirements.txt`; opcional TA-Lib (comentado).
- **Frontend**: `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000`) para apuntar a la API; scripts npm (`dev`, `build`, `start`).
- **Setup recomendado**:
  1. Backend: `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env`.
  2. Poblar base: `python main.py` (descarga datos iniciales).
  3. Actualizar CVD (opcional): `python update_cvd_data.py`.
  4. Lanzar API: `python server.py` (Uvicorn en `0.0.0.0:8000`).
  5. Frontend: `cd frontend && npm install && npm run dev` (por defecto en `http://localhost:3000`).

## 6. Puntos de entrada y ejecución
- **Scripts CLI**:
  - `backend/main.py`: ingesta OHLCV inicial/incremental.
  - `backend/run_scanner.py`: ejecución manual del escáner de señales (output en consola).
  - `backend/update_cvd_data.py`: cálculo/peristencia CVD por vela.
- **Servicios**:
  - `backend/server.py` → `uvicorn src.api.app:app` para exponer la API.
  - Frontend se ejecuta con `npm run dev|build|start` apuntando a la API.

## 7. Estado del código y oportunidades de mejora
- **Fortalezas**:
  - Código modular con responsabilidades claras (data, indicadores, señales, API).
  - Buen uso de tipado (dataclasses, Pydantic) y logging consistente.
  - Suite de tests amplia que cubre componentes críticos (indicadores, motor de señales, patrones).
  - Frontend tipado y desacoplado mediante hooks SWR + componentes reutilizables.
- **Áreas de mejora**:
  - **Persistencia**: `DataStorage` crea engine por instancia; considerar factorizar a singleton/pool para reducir overhead y habilitar conexiones async cuando se ejecute bajo Uvicorn con alta concurrencia.
  - **Performance**: `SignalEngine` se ejecuta sin cache en cada request `/api/signals/current`; evaluar ejecución programada y cache (Redis/memoria) para evitar cálculos pesados bajo tráfico.
  - **Gestión de errores API**: retornar códigos/razones más específicos cuando faltan datos (actualmente HTTP 503/404 genéricos).
  - **Infraestructura**: falta orquestador para tareas periódicas (ingesta OHLCV, CVD, signals). Considerar scheduler externo (Celery, cron) o background tasks.
  - **Seguridad/config**: manejo de API keys (si se extiende a endpoints privados) y validación de inputs (`SYMBOLS`, `TIMEFRAMES`) desde entorno.
  - **Frontend**: ausencia de vistas para histórico de señales o alertas push; oportunidad de incorporar WebSockets o SSE.

---
Documento generado como base de referencia para futuras iteraciones del bot BC4.
