# Binance OHLCV Data Pipeline

Pipeline básico para descargar y almacenar datos históricos de velas (OHLCV) desde el exchange Binance. Este módulo es la base para el sistema de señales de trading multi-timeframe (4H estructura + 1H entradas).

## Requisitos

- Python 3.10+
- Conexión a Internet (para acceder a la API pública de Binance)

## Configuración

```bash
# Clonar o acceder al repositorio y entrar a la carpeta backend
cd backend

# (Opcional) Crear un entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Variables de entorno

Copiar el archivo `.env.example` y adaptarlo si fuera necesario:

```bash
cp .env.example .env
```

Valores por defecto:

```env
EXCHANGE=binance
SYMBOLS=BTC/USDT,ETH/USDT,SOL/USDT
TIMEFRAMES=1h,4h
DEFAULT_LIMIT=100
DB_PATH=crypto_data.db
```

## Uso

```bash
python main.py
```

El script realizará las siguientes acciones:

1. Descargar las últimas 100 velas para BTC/USDT, ETH/USDT y SOL/USDT en timeframes de 1 hora y 4 horas.
2. Validar los datos recibidos (sin gaps ni valores nulos) y convertir los timestamps a UTC legible.
3. Guardar la información en la base de datos SQLite definida en `DB_PATH` (`crypto_data.db` por defecto).
4. Mostrar un resumen en consola con el rango temporal descargado y la cantidad total de registros almacenados.
5. Imprimir las últimas 5 velas de BTC/USDT en timeframe 1h como ejemplo.

Ejemplo de salida:

```
✓ BTC/USDT 4h: 100 velas descargadas (2024-01-01 00:00 → 2024-01-17 16:00)
✓ BTC/USDT 1h: 100 velas descargadas (2024-01-13 12:00 → 2024-01-17 15:00)
✓ ETH/USDT 4h: 100 velas descargadas (2024-01-01 00:00 → 2024-01-17 16:00)
✓ ETH/USDT 1h: 100 velas descargadas (2024-01-13 12:00 → 2024-01-17 15:00)
✓ SOL/USDT 4h: 100 velas descargadas (2024-01-01 00:00 → 2024-01-17 16:00)
✓ SOL/USDT 1h: 100 velas descargadas (2024-01-13 12:00 → 2024-01-17 15:00)
Total: 600 registros almacenados

Últimas 5 velas BTC/USDT 1h:
 datetime            open    high     low   close  volume
 2024-01-17 11:00  42870.0  43000.0  42700.0  42950.0  152.35
 ...
```

Los logs informativos se muestran en la consola durante la ejecución para facilitar el monitoreo.

## Almacenamiento de datos

Los datos se persisten en SQLite utilizando SQLAlchemy con la siguiente estructura de tabla (`ohlcv`):

| Columna    | Tipo    | Descripción                                   |
|------------|---------|-----------------------------------------------|
| id         | Integer | Primary Key                                   |
| symbol     | String  | Par de trading (e.g. `BTC/USDT`)              |
| timeframe  | String  | Timeframe (e.g. `1h`, `4h`)                   |
| timestamp  | Integer | Unix timestamp (UTC, en segundos)             |
| open       | Float   | Precio de apertura                            |
| high       | Float   | Precio máximo                                 |
| low        | Float   | Precio mínimo                                 |
| close      | Float   | Precio de cierre                              |
| volume     | Float   | Volumen negociado                             |
| created_at | DateTime| Fecha/hora de inserción del registro (UTC)    |

Existe una restricción `UNIQUE(symbol, timeframe, timestamp)` para evitar duplicados y permitir actualizaciones incrementales.

Puedes inspeccionar la base de datos con cualquier visor de SQLite o utilizando herramientas como `sqlite3`.

## Tests

Ejecutar los tests básicos con `pytest`:

```bash
pytest tests
```

Se validan:

- Conexión y obtención de datos desde la API de Binance.
- Coordinación y validación de descargas múltiples con `DataFetcher`.

## Próximos pasos (Phase 1.2)

- Cálculo de indicadores técnicos (SMA, EMA, RSI, etc.).
- Integración de señales multi-timeframe.
- Exposición de datos mediante API para la webapp.
