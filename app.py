import streamlit as st
import pandas as pd
import plotly.express as px
import os
from src.etl import ejecutar_pipeline
from src.plot import (
    plot_serie_temporal_articulos_por_anho, 
    plot_histograma_coautores,
    plot_scatter_subcomunidades,
    plot_distribucion_subcomunidades,
    plot_heatmap_produccion_subcomunidades,
    plot_bar_top_20e
)

# Directorio exacto donde se está ejecutando el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------
# 1. Configuración de la página Streamlit
# --------------------------------------------------------
st.set_page_config(page_title="Dashboard Repositorio Institucional ULA", layout="wide")


# --------------------------------------------------------
# 2. Carga de datos (Usa caché para que la app sea rápida): CARGA del archivo Parquet como resultado del pipeline, previamente pasado por src/etl.py
# --------------------------------------------------------
# Como el pipeline se ejecuta por CRONTAB, cargamos directamente el archivo Parquet (más rápido)
@st.cache_data
def cargar_datos():
    archivo_parquet = os.path.join(BASE_DIR, "data/articulos_procesados.parquet")
    return pd.read_parquet( archivo_parquet )

df = cargar_datos()


# --------------------------------------------------------
# 3. Barra Lateral (Fitros interactivos para el usuario) : FILTROS
# --------------------------------------------------------
st.sidebar.header("⚙️ Filtros de Items")

# 1. Filtrar Comunidad Principal
options_commds = ["***Combinado***", "Facultades", "Revistas"]
comunidadds = st.sidebar.radio(
    "¿Comunidad DSpace?",
    options_commds,
    captions=[" 🔀 Revistas y Facultades", " 🎓 Facultades y Núcleos.", " 📰 Revistas Universitarias."],
    index=0  # Por omitión todos los items del set de datos
)
df_comm_filtrada = df
if comunidadds:
    opc_comm_i = options_commds.index(comunidadds)
    if opc_comm_i == 1 :
        df_comm_filtrada = df.query("comm == 'comm1'") #facultades
    if opc_comm_i == 2:
        df_comm_filtrada = df.query("comm == 'comm4105'") #revistas

# 2. Buscador de texto libre por titulo o palabra clave: 
busqueda = st.sidebar.text_input("🌟🔍 Buscar por título o palabra clave:", "")

# 3. Buscador de texto libre por autor: 
busqueda1 = st.sidebar.text_input("👤🔍 Buscar por autor:", "")

# 4. Rango dinámico por años de publicación
min_anho = int(df_comm_filtrada["Año"].min())
max_anho = int(df_comm_filtrada["Año"].max())
rango_anhos = st.sidebar.slider(
    "🗓️ Selecciona el rango de años de publicación:",
    min_value=min_anho,
    max_value=max_anho,
    value=(min_anho, max_anho) # Tupla con el valor inicial (min año, max año)
)

# 5. Filtro por Subcomunidad (Facultades o Revistas)
subcomunidades_disponibles = sorted(df_comm_filtrada['subcomunidad'].unique())
subcomunidades_seleccionadas = st.sidebar.multiselect("👥 Selecciona las Comunidades (Facultad/Revista):", subcomunidades_disponibles, default=subcomunidades_disponibles)

# --------------------------------------------------------
# Aplicando los filtros ...

# filtramos por Año y Subcomunidad
df_filtrado = df_comm_filtrada[
                (df_comm_filtrada['Año'].between(rango_anhos[0],rango_anhos[1])) & 
                (df_comm_filtrada['subcomunidad'].isin(subcomunidades_seleccionadas))
                ]

# Si el usuario escribió algo en 'Titulo' o 'Palabra Clave', filtramos por coincidencia de texto
if busqueda:
    # buscamos en 'Articulo' o en 'PalabrasClaves' sin importar mayúsculas/minúsculas
    condicion_titulo = df_filtrado['articulo'].str.contains(busqueda, case=False, na=False)
    condicion_keyword = df_filtrado['palabrasclaves'].str.contains(busqueda, case=False, na=False)
    df_filtrado = df_filtrado[condicion_titulo | condicion_keyword]
    
# Si el usuario escribió algo en filtro "Autor", filtramos por coincidencia de texto
if busqueda1:
    # El filtro busca en 'Autor' sin importar mayúsculas/minúsculas
    condicion_autor = df_filtrado['autor'].str.contains(busqueda1, case=False, na=False)
    df_filtrado = df_filtrado[condicion_autor]
    

# Generar dataframes 'Palabras claves' basados en los datos filtrados
df_keywords = df_filtrado.assign(palabrasclaves=df_filtrado['palabrasclaves'].str.split(';')).explode('palabrasclaves')
df_keywords['palabrasclaves'] = df_keywords['palabrasclaves'].str.strip()

# Generar dataframes 'Autor' basados en los datos filtrados
df_authors = df_filtrado.assign(autor=df_filtrado['autor'].str.split(';')).explode('autor')
df_authors['autor'] = df_authors['autor'].str.strip()
# --------------------------------------------------------


# 2. Procesar los datos (Top 10 Subcomunidades y Otros)
df_agrupado = df_filtrado.groupby('subcomunidad')['subcomunidad'].count()
df_ordenado = df_agrupado.sort_values(ascending=False)

top_15 = df_ordenado.head(15)
otros = df_ordenado.iloc[15:].sum()
datos_finales = pd.concat([top_15, pd.Series({'Otros': otros})])
if otros == 0:
    datos_finales = datos_finales.drop('Otros')
    
# Convert Series to DataFrame
df_subcomunidades = datos_finales.reset_index()
df_subcomunidades.columns = ['Subcomunidad', 'Cantidad Publicaciones']


# nuevas columnas aplicando str(x).split(';') sobre Autores y Palabras Clave

# Contar autores por artículo de forma dinámica sobre los datos filtrados
df_filtrado['Num_Autores'] = df_filtrado['autor'].apply(lambda x: len(str(x).split(';')))

# Contar palabras clave por artículo de forma dinámica sobre los datos filtrados
df_filtrado['Num_PC'] = df_filtrado['palabrasclaves'].apply(lambda x: len(str(x).split(';')))


# Mostrar un botón en la barra lateral
with st.sidebar:
    # ~ st.write("### Contacto")
    st.divider()
    st.write("")
    st.link_button("Autor: DU", "https://www.linkedin.com/in/diego-uzc-j/")

# --------------------------------------------------------
# 4. CUERPO PRINCIPAL DEL DASHBOARD: Indicadores Clave de Desempeño
# --------------------------------------------------------
st.title("📊 Dashboard de Ciencia de Datos: Items de DSpace SaberULA")
st.markdown("Analiza **una sección** de los items del *Repositorio Institucional de la Universidad de Los Andes*, **SaberULA** (www.saber.ula.ve), compuesta principalmente por artículos científicos de las comunidades DSpace de revistas y facultades ULA: Muestra graficamente tendencias temporales, análisis de coautores, proporción de subcomunidades, densidad temática con Heatmaps, palabras clave más utilizadas y autores con mayor publicación.")

# Fila de Métricas Clave (KPIs)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Artículos", len(df_filtrado))
with col2:
    st.metric("Subcomunidades Activas", df_filtrado['subcomunidad'].nunique())
with col3:
    # Cálculo dinámico de promedio de autores
    num_autores = df_filtrado['autor'].apply(lambda x: len(str(x).split(';')))
    st.metric("Promedio Autores/Artículos", f"{num_autores.mean():.1f}" if not num_autores.empty else "0")
with col4:
    # Obtener lista de autores
    todos_autores = df_filtrado['autor'].str.split(';').explode()
    autores_unicos = todos_autores.str.strip().unique() # .str.strip() elimina espacios extra, unique() eliminamos duplicados
    st.metric("Cantidad Autores", len(autores_unicos) )

st.divider()
# --------------------------------------------------------




# --------------------------------------------------------
# 5. CUERPO PRINCIPAL DEL DASHBOARD: Pestañas con Gráficos y Tablas
# --------------------------------------------------------    
# Crear pestañas interactivas
tab_tendencia_temporal, tab_analisis_coautores, tab_comunidades, densidad_tematica_comm, tab_top_palabrasclave, tab_top_autores, tab_tabladatos = st.tabs([
                                                "📈 Tendencias Temporales", 
                                                "👥 Análisis de Coautores", 
                                                "🤝 Comunidades", 
                                                "🌡️ Densidad Temática", 
                                                "🏷️ Top Palabras Clave", 
                                                "👤 Top Autores",
                                                "🔍 Vista de Datos Filtrados"
                                                ])


# --------------------------------------------------------
with tab_tendencia_temporal:
    # Línea de evolución en el tiempo
    st.write("¿Cómo ha sido el crecimiento histórico de publicación cada año? ¿Cómo va el crecimiento acumulado?")
    st.subheader("📈 Evolución Temporal de Publicaciones")
    if not df_filtrado.empty:
        articulos_por_año = df_filtrado['Año'].value_counts().sort_index()
        
        # 1. Generar y mostrar gráfico de lineas
        fig1 = plot_serie_temporal_articulos_por_anho(df_filtrado, articulos_por_año.reset_index())
        st.plotly_chart(fig1)
        
        st.divider()
        
        col1_tab_tmp, col3_tab_tmp = st.columns(2)
        with col1_tab_tmp:
            # datos tabulados
            st.subheader("Producción anual")
            st.dataframe(articulos_por_año, use_container_width=True)
        with col3_tab_tmp:
            # 2. Gráfico de área interactivo: Producción acumulado por años
            st.subheader("⛰️ ️Acumulado")
            st.area_chart(articulos_por_año.cumsum(), color='#006a8c')
        
    else:
        st.warning("No hay datos para mostrar con los filtros actuales.")
        
# --------------------------------------------------------
with tab_analisis_coautores:
    # 3. Histograma
    st.write("¿Cuál es la tendencia de colaboración? ¿Cuál es el tamaño promedio de los equipos por subcomunidad?")
    st.subheader("👥 Distribución de Autores por Artículo")

    if not df_filtrado.empty:
        
        # Generar la figura usando la función externa del histograma
        fig_autores = plot_histograma_coautores(df_filtrado)

        # Gráfico Histograma de forma responsiva
        st.plotly_chart(fig_autores, use_container_width=True)
                
        # Pequeño dato estadístico interactivo debajo del gráfico
        st.caption(f"💡 En promedio, los artículos de esta selección cuentan con **{df_filtrado['Num_Autores'].mean():.1f}** autores.")
        
        st.divider()
        
        st.info("¿Cuál es la relación de facultades/revistas con promedio de autores?")        
        
        # 4. Dispersión. Correlación entre variables
        # Agrupar por comunidad: promedio de autores Y total de artículos
        comunidades = (
            df_filtrado.groupby("subcomunidad")
            .agg(
                promedio_autores=("Num_Autores", "mean"),
                total_articulos=("id", "count"),
            )
            .reset_index()
        )

        # Generar la figura usando la función externa del gráfico de dispesión
        fig = plot_scatter_subcomunidades(comunidades)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("No hay datos para calcular la distribución.")
        
# --------------------------------------------------------
with tab_comunidades:
    # 5. Pie
    st.write("¿Cuál es la proporción de producción de publicaciones por facultad/revista?")
    st.subheader("🤝 Distribución de artículos en Subcomunidades")
    if not df_filtrado.empty:
        # Gráfico de pastel (Pie chart)
        fig_pie = plot_distribucion_subcomunidades(df_subcomunidades)
        
        # Renderizado nativo en Streamlit
        st.plotly_chart(fig_pie, use_container_width=True)
        
    else:
        st.warning("No hay datos para mostrar con los filtros actuales.")
        
    st.divider()
    
    st.subheader("Comunidades: Facultades o Revistas")
    # Mostrar DataFrame
    st.dataframe(df_subcomunidades, use_container_width=True)
    
# --------------------------------------------------------

with densidad_tematica_comm:
    # 6. Heatmap
    st.write("¿En qué años se ha tenido mayor producción en cada subcomunidad?")    
    st.subheader("🌡️ Mapa de Calor: Intensidad de Publicación por Subcomunidad")

    if not df_filtrado.empty and df_filtrado['subcomunidad'].nunique() > 0:
        # Crear una matriz cruzada entre Año y Subtemática
        matriz_cruzada = pd.crosstab(df_filtrado['subcomunidad'], df_filtrado['Año'])
        filas_por_pagina = 10 
        total_filas = len(matriz_cruzada)

        # Crear los botones horizontales (paginado cuando hay más de 10 filas)
        cant_bloques = (total_filas // filas_por_pagina) + (1 if total_filas % filas_por_pagina != 0 else 0) # equivale a math.ceil(total_filas / filas_por_pagina)
        options = range(1, cant_bloques + 1 )
        print('total filas:',total_filas, 'cant: ',cant_bloques, options)
        opcion_seleccionada = st.segmented_control(
            "Selecciona la sección del heatmap:",
            options,#=[1, 2, 3, 4]
            format_func=lambda x: f"Heatmap {x}",
            default=1  # Bloque seleccionado por defecto
        )
        # calculando bloque seleccionado del heatmap
        print('opcion_seleccionada:',opcion_seleccionada)
        if opcion_seleccionada is None:
            opcion_seleccionada = 1
        inicio = (opcion_seleccionada - 1) * filas_por_pagina
        fin = inicio + filas_por_pagina
        df_bloque = matriz_cruzada.iloc[inicio:fin]

        # Creando gráficos Heatmap desde función en src/plot.py
        fig_heatmap = plot_heatmap_produccion_subcomunidades(df_bloque)

        # Mostrar gráfico en Streamlit
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
    else:
        st.warning("Se necesitan múltiples subtemáticas y años para generar el mapa de calor.")


# --------------------------------------------------------
with tab_top_palabrasclave:
    # 7. Bar
    st.write("¿Cuáles son los temas, disciplinas y palabras clave más populares investigados?")
    st.subheader("🏷️ Top Palabras Clave")
    if not df_keywords.empty and df_keywords['palabrasclaves'].notna().any():
        fig2 = plot_bar_top_20e(df_keywords, 'palabrasclaves')
        st.plotly_chart(fig2)        
    else:
        st.warning("No hay palabras clave en la selección.")

    st.divider()
    
    st.subheader("Palabras Clave y cantidad de publicaciones")
    todas_palabrasclave = df_filtrado['palabrasclaves'].str.split(';').explode().str.strip()
    frecuencia_palabras = todas_palabrasclave.value_counts()
    # Mostrar DataFrame
    st.dataframe(frecuencia_palabras, use_container_width=True)
    
    
# --------------------------------------------------------
with tab_top_autores:
    # 8. Bar
    st.write("¿Qué autores publican más?")
    st.subheader("👤 Top Autores según cantidad de publicaciones")
    if not df_authors.empty and df_authors['autor'].notna().any():
        fig3 = plot_bar_top_20e(df_keywords, 'autor')
        st.plotly_chart(fig3)
    else:
        st.warning("No hay autor en la selección.")

    st.divider()
    
    st.subheader("Autores y cantidad de publicaciones")
    todos_autores = df_filtrado['autor'].str.split(';').explode().str.strip()
    frecuencia_autores = todos_autores.value_counts() #contar repeticiones de cada autor
    # Mostrar DataFrame
    st.dataframe(frecuencia_autores, use_container_width=True)

        
# --------------------------------------------------------

with tab_tabladatos:
    st.write("¿Cuál es el conjunto de datos con los filtros aplicados en este momento?")
    
    # Explorador de datos crudos al final
    st.subheader("🔍 Vista de Datos Filtrados")
    
    # colocando nombres de columnas en formato más amigable para el usuario
    df_filtrado["comm"] = df_filtrado["comm"].replace({"comm1": "Facultad", "comm4105": "Revista"}) 
    df_filtrado.rename(columns={'comm': 'Comunidad'}, inplace=True)
    df_filtrado.rename(columns={'id': 'ID'}, inplace=True)
    df_filtrado.rename(columns={'articulo': 'Artículo'}, inplace=True)
    df_filtrado.rename(columns={'subcomunidad': 'Facultad/Revista'}, inplace=True)
    df_filtrado.rename(columns={'palabrasclaves': 'Palabras Claves'}, inplace=True)
    df_filtrado.rename(columns={'autor': 'Autores'}, inplace=True)
    df_filtrado.rename(columns={'fecha': 'Fecha'}, inplace=True)
    # Mostrar DataFrame
    st.dataframe(df_filtrado, use_container_width=True)


st.markdown('<div style="width: 0px; height: 0px; overflow: hidden;"><a href="https://www.linkedin.com/in/diego-uzc-j/" hidden>www.linkedin.com/in/diego-uzc-j</a></div>', unsafe_allow_html=True)
