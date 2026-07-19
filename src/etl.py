import logging
import os
import pandas as pd

#ruta absoluta
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SRC_DIR)                  

# --------------------------------------------------------
# Configuración del Logging
# --------------------------------------------------------
# Crear carpeta de logs si no existe
RUTA_LOGS = os.path.join(BASE_DIR, "logs")
os.makedirs(RUTA_LOGS, exist_ok=True)
RUTA_LOGS_FILE = os.path.join(BASE_DIR, "logs", "etl_pipeline.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(RUTA_LOGS_FILE, encoding="utf-8"),
        logging.StreamHandler(),  # Muestra el log también en consola
    ],
)


# --------------------------------------------------------
# Fases del Pipeline ETL
# --------------------------------------------------------


def extraer_datos(ruta_csv: str) -> pd.DataFrame:
    """Fase E: Extrae los datos verificando la existencia del archivo."""
    if not os.path.exists(ruta_csv):
        logging.error(f"Archivo no encontrado en la ruta: {ruta_csv}")
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_csv}")

    logging.info(f"Cargando datos desde archivo de origen: {ruta_csv}...")
    df = pd.read_csv(ruta_csv)

    # Validación 1: Verificar que el archivo no venga completamente vacío
    if df.empty:
        logging.error("El archivo CSV cargado está vacío.")
        raise ValueError("El DataFrame origen no contiene filas.")

    logging.info(f"Extracción exitosa. Registros iniciales: {len(df)}")
    return df


def transformar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Fase T: Limpia fechas, genera nuevas columnas y valida integridad."""
    logging.info("Iniciando fase de transformación y limpieza...")

    # Validación 2: Verificar columnas críticas requeridas
    columnas_requeridas = ["fecha"]
    for col in columnas_requeridas:
        if col not in df.columns:
            logging.error(f"Falta la columna obligatoria '{col}' en los datos.")
            raise KeyError(f"Columna faltante: '{col}'")

    df_limpio = df.copy()

    # Identificar y eliminar filas con formato de fecha incorrecto
    patron = r"^\d{4}-\d{2}-\d{2}$"
    filtro_invalidos = ~df_limpio["fecha"].str.match(patron, na=False)
    indices_a_eliminar = df_limpio[filtro_invalidos].index

    if len(indices_a_eliminar) > 0:
        logging.warning(
            f"Se detectaron {len(indices_a_eliminar)} filas con fechas inválidas. Índices: {indices_a_eliminar.tolist()}"
        )
        df_limpio.drop(indices_a_eliminar, inplace=True)
    else:
        logging.info("No se encontraron registros con formato de fecha corrupto.")

    # Conversión de tipos y nueva columna de año
    df_limpio["fecha"] = pd.to_datetime(df_limpio["fecha"], errors="coerce")
    df_limpio["Año"] = df_limpio["fecha"].dt.year

    # Validación 3: Alerta si tras la limpieza el DataFrame se quedó sin registros
    if df_limpio.empty:
        logging.warning(
            "La transformación eliminó todos los registros disponibles debido a fechas corruptas."
        )

    logging.info(f"Transformación completada. Registros actuales: {len(df_limpio)}")
    return df_limpio


def cargar_a_parquet(df: pd.DataFrame, ruta_parquet: str) -> None:
    """Fase L: Carga y persiste los datos con validaciones post-proceso."""
    # Validación 4: Evitar sobreescribir con datos rotos o nulos en columnas clave
    conteo_nulos_anio = df["Año"].isna().sum()
    if conteo_nulos_anio > 0:
        logging.warning(
            f"Se detectaron {conteo_nulos_anio} valores nulos (NaN) en la columna calculada 'Año'."
        )

    logging.info(f"Guardando archivo Parquet en: {ruta_parquet}...")
    os.makedirs(os.path.dirname(ruta_parquet), exist_ok=True)

    # Se requiere la librería 'pyarrow' o 'fastparquet' en tu entorno python
    df.to_parquet(ruta_parquet, index=False)
    logging.info("¡Carga exitosa! Archivo Parquet creado de manera limpia.")


def ejecutar_pipeline(ruta_entrada: str, ruta_salida: str) -> pd.DataFrame:
    """Orquesta la ejecución de las fases controlando errores críticos."""
    logging.info("---------------------------------------")
    logging.info("| Iniciando Ejecución del Pipeline ETL")
    logging.info("---------------------------------------")

    try:
        df_e = extraer_datos(ruta_entrada)
        df_t = transformar_datos(df_e)
        cargar_a_parquet(df_t, ruta_salida)

        logging.info("---------------------------------------")
        logging.info("| Pipeline Completado con Éxito")
        logging.info("---------------------------------------")
        return df_t

    except Exception as e:
        logging.critical(
            f"El pipeline falló de forma crítica durante la ejecución: {str(e)}",
            exc_info=True,
        )
        raise e


if __name__ == "__main__":
    # Configuración de prueba de ejecución directa
    RUTA_CSV = os.path.join(BASE_DIR, "data", "articulos_comms_fac_y_rev.csv")
    RUTA_PARQUET = os.path.join(BASE_DIR, "data", "articulos_procesados.parquet")

    # Ejecutar pipeline principal
    df_final = ejecutar_pipeline(RUTA_CSV, RUTA_PARQUET)
