"""
db.py - La "memoria" del agente (SQLite: un solo archivo, sin servidor).

Tablas:
  precios            -> velas diarias (OHLCV) de cada ticker
  versiones_params   -> cada configuración de parámetros que usaste
  decisiones         -> DIARIO del agente: qué decidió, por qué y con qué datos
  operaciones        -> trades simulados (paper): entrada, stop, objetivo, salida, resultado
  equity             -> valor de la cartera simulada día a día
"""
import sqlite3, json, hashlib
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS precios (
    ticker TEXT, fecha TEXT,
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    PRIMARY KEY (ticker, fecha)
);

CREATE TABLE IF NOT EXISTS versiones_params (
    version_id   TEXT PRIMARY KEY,      -- hash de los parámetros
    nombre       TEXT,
    creada       TEXT DEFAULT (datetime('now','localtime')),
    params_json  TEXT
);

CREATE TABLE IF NOT EXISTS decisiones (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha        TEXT,                  -- fecha de la vela analizada
    ticker       TEXT,
    accion       TEXT,                  -- COMPRAR / VENDER / MANTENER / NO_OPERAR
    motivo       TEXT,                  -- explicación legible
    datos_json   TEXT,                  -- indicadores del momento (RSI, SMA, ATR...)
    version_id   TEXT REFERENCES versiones_params(version_id),
    registrada   TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS operaciones (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker         TEXT,
    cedear         TEXT,
    version_id     TEXT,
    fecha_entrada  TEXT,
    precio_entrada REAL,
    precio_entrada_cedear_ars REAL,
    cantidad       REAL,
    stop           REAL,
    objetivo       REAL,
    riesgo_usd     REAL,                -- cuánto se arriesgaba (1R)
    fecha_salida   TEXT,
    precio_salida  REAL,
    motivo_salida  TEXT,                -- STOP / OBJETIVO / TIEMPO / SEÑAL
    pnl_usd        REAL,
    r_multiple     REAL,                -- resultado medido en "R"
    estado         TEXT DEFAULT 'ABIERTA'
);

CREATE TABLE IF NOT EXISTS ordenes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_senal  TEXT,                  -- cierre en que apareció la señal
    ticker       TEXT,
    atr          REAL,
    prioridad    REAL,
    version_id   TEXT,
    estado       TEXT DEFAULT 'PENDIENTE',   -- PENDIENTE / EJECUTADA / DESCARTADA
    detalle      TEXT
);

CREATE TABLE IF NOT EXISTS cuenta (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    capital_inicial REAL,
    efectivo        REAL,
    inicio          TEXT,
    ultima_fecha    TEXT                -- última vela procesada por el paper trading
);

-- Momentum ("booms del momento")
CREATE TABLE IF NOT EXISTS estado_motor (
    nombre        TEXT PRIMARY KEY,     -- 'momentum'
    ultima_fecha  TEXT,
    estado_json   TEXT                  -- efectivo, posiciones, orden pendiente, etc.
);

CREATE TABLE IF NOT EXISTS mom_operaciones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha       TEXT,
    ticker      TEXT,
    lado        TEXT,                   -- COMPRA / VENTA
    cantidad    REAL,
    precio      REAL,
    monto_usd   REAL,
    motivo      TEXT,
    retorno     REAL,                   -- en ventas: resultado de la posición
    version_id  TEXT
);

CREATE TABLE IF NOT EXISTS ranking (
    fecha    TEXT,
    ticker   TEXT,
    sector   TEXT,
    puesto   INTEGER,
    puntaje  REAL,
    r21 REAL, r63 REAL, r126 REAL, r252 REAL,
    PRIMARY KEY (fecha, ticker)
);

CREATE TABLE IF NOT EXISTS equity (
    fecha      TEXT,
    version_id TEXT,
    efectivo   REAL,
    invertido  REAL,
    total      REAL,
    PRIMARY KEY (fecha, version_id)
);
"""


# Columnas agregadas después de la primera versión (se crean si faltan)
COLUMNAS_EXTRA = {
    "operaciones": {"sector": "TEXT", "stop_inicial": "REAL", "dias": "INTEGER DEFAULT 0",
                    "maximo": "REAL", "costo_total": "REAL"},
}


def conectar(ruta: str) -> sqlite3.Connection:
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.executescript(ESQUEMA)
    for tabla, cols in COLUMNAS_EXTRA.items():
        existentes = {f[1] for f in con.execute(f"PRAGMA table_info({tabla})")}
        for col, tipo in cols.items():
            if col not in existentes:
                con.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
    con.commit()
    return con


def registrar_version(con, cfg: dict, claves=("estrategia", "riesgo"), nombre=None) -> str:
    """Guarda la configuración actual y devuelve su ID.
    Si no cambiaste nada, reutiliza el mismo ID.
    `claves`: secciones de config.yaml que definen la estrategia (swing o momentum)."""
    params = {k: cfg[k] for k in claves}
    texto = json.dumps(params, sort_keys=True)
    version_id = hashlib.sha1(texto.encode()).hexdigest()[:8]
    con.execute(
        "INSERT OR IGNORE INTO versiones_params (version_id, nombre, params_json) VALUES (?,?,?)",
        (version_id, nombre or cfg.get("nombre_version", ""), texto),
    )
    con.commit()
    return version_id


def guardar_precios(con, ticker: str, df) -> int:
    """Inserta/actualiza velas diarias. df: índice fecha, columnas Open/High/Low/Close/Volume."""
    filas = [
        (ticker, idx.strftime("%Y-%m-%d"), float(r.Open), float(r.High),
         float(r.Low), float(r.Close), float(r.Volume))
        for idx, r in df.iterrows()
    ]
    con.executemany("INSERT OR REPLACE INTO precios VALUES (?,?,?,?,?,?,?)", filas)
    con.commit()
    return len(filas)


def registrar_decision(con, fecha, ticker, accion, motivo, datos: dict, version_id):
    con.execute(
        "INSERT INTO decisiones (fecha, ticker, accion, motivo, datos_json, version_id) VALUES (?,?,?,?,?,?)",
        (fecha, ticker, accion, motivo, json.dumps(datos), version_id),
    )
    con.commit()
