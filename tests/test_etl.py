import pytest
import pandas as pd
import numpy as np
from src.etl import extraer_datos, transformar_datos

# --------------------------------------------------------
# Datos de prueba (Fixtures)
# --------------------------------------------------------
@pytest.fixture
def datos_validos_csv(tmp_path):
    """Crea un archivo CSV temporal con datos correctos e incorrectos."""
    ruta_archivo = tmp_path / "datos_prueba.csv"
    data = {
        "fecha": ["2026-01-01", "fecha-invalida", "2026-12-31", np.nan],
        "articulo": ["A", "B", "C", "D"]
    }
    df = pd.DataFrame(data)
    df.to_csv(ruta_archivo, index=False)
    return str(ruta_archivo)

@pytest.fixture
def datos_vacios_csv(tmp_path):
    """Crea un archivo CSV vacío."""
    ruta_archivo = tmp_path / "vacio.csv"
    df = pd.DataFrame(columns=["fecha", "articulo"])
    df.to_csv(ruta_archivo, index=False)
    return str(ruta_archivo)


# --------------------------------------------------------
# Pruebas Unitarias
# --------------------------------------------------------

def test_extraer_datos_error_archivo_no_existe():
    """Valida que falle con un error claro si el archivo no existe."""
    with pytest.raises(FileNotFoundError):
        extraer_datos("ruta_que_no_existe/archivo_no_existe.csv")

def test_extraer_datos_vacio(datos_vacios_csv):
    """Valida que falle si el archivo CSV no contiene registros."""
    with pytest.raises(ValueError, match="El DataFrame origen no contiene filas"):
        extraer_datos(datos_vacios_csv)

def test_transformar_datos_limpieza_fechas(datos_validos_csv):
    """Valida la eliminación de formatos incorrectos y creación de columna Año."""
    df_inicial = pd.read_csv(datos_validos_csv)
    df_resultado = transformar_datos(df_inicial)

    # El CSV inicial tiene 4 filas. 2 tienen fechas inválidas (la cadena corrupta y el NaN)
    assert len(df_resultado) == 2
    
    # Comprobar que la columna Año se calculó correctamente
    assert "Año" in df_resultado.columns
    assert list(df_resultado["Año"].unique()) == [2026]

def test_transformar_datos_falta_columna_critica():
    """Valida que falle si el DataFrame no tiene la columna 'fecha'."""
    df_incorrecto = pd.DataFrame({"stats_descargas": [1999, 2005]})
    with pytest.raises(KeyError):
        transformar_datos(df_incorrecto)
