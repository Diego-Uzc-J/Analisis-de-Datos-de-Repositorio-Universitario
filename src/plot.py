import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def plot_serie_temporal_articulos_por_anho(df: pd.DataFrame, serieanhos: pd.Series) -> go.Figure:
    """
    Con la cantidad de artículos por año, genera un gráfico de líneas interactivo.
    """
    serieanhos.columns = ['Año', 'Artículos']
    
    # Crear gráfico de líneas interactivo
    fig = px.line(
        serieanhos, 
        x='Año', 
        y='Artículos', 
        markers=True,
        title="Artículos por Año"
    )
    
    # Forzar enteros en el eje X
    fig.update_xaxes(dtick=1, tickformat="d")
    
    return fig

def plot_histograma_coautores(df_filtrado):
    """
    Crea un histograma interactivo con Plotly. Para ver la concentración de valores.
    """
    # 1. Crear el histograma con Plotly Express
    fig_autores = px.histogram(
        df_filtrado, 
        x='Num_Autores',
        labels={'Num_Autores': 'Cantidad de Autores en un Artículo', 'count': 'Número de Artículos'},
        color_discrete_sequence=["#4A90E2"]
    )

    # 2. Configurar ejes para que actúen de forma discreta y con números enteros
    fig_autores.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),
        yaxis_title="Número de Artículos",
        bargap=0.1,
        height=250,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    return fig_autores

def plot_scatter_subcomunidades(comunidades):
    """
    Crea un gráfico de dispersión interactivo con Plotly. Con la idea de ver la correlación que hay entre las subcomunidades y el promedio de autores.
    """
    fig = px.scatter(
        comunidades,
        x="total_articulos",
        y="promedio_autores",
        color="subcomunidad",
        title="Promedio de Autores vs. Volumen de Artículos por Comunidad",
        labels={
            "total_articulos": "Total de Artículos Publicados",
            "promedio_autores": "Promedio de Autores por Artículo",
            "subcomunidad": "Subcomunidad",
        },
    )
    return fig


def plot_distribucion_subcomunidades(df):
    """
    Crea un gráfico de pastel interactivo con Plotly. Con el objetivo de ver como se distribuyen los datos entre las comunidades.
    """
    df.columns = ['Subcomunidad', 'Cantidad Publicaciones']
    
    # Creamos el gráfico de pastel (Pie chart) utilizando Plotly Express
    fig_pie = px.pie(
        df, 
        names="Subcomunidad", 
        values="Cantidad Publicaciones", 
        title="Distribución de Artículos por Subcomunidad",
        hole=0.3, # Efecto tipo dona
        color_discrete_sequence=px.colors.qualitative.Set1,
        width=600,
        height=600
    )
    
    return fig_pie

def plot_heatmap_produccion_subcomunidades(df_bloque):
    """
    Crea un gráfico de heatmap interactivo con Plotly. Para facilitar la identificación patrones, tendencias y valores extremos a través de escala de colores.
    """
    # Acortar etiquetas largas
    labels = df_bloque.index.astype(str)
    truncated_labels = [label[:30] + '...' if len(label) > 30 else label for label in labels]

    # Crear el heatmap interactivo con Plotly Express
    fig = px.imshow(
        df_bloque,
        labels=dict(x="Año", y="Subcomunidad", color="Producción"),
        x=df_bloque.columns.astype(str),
        y=truncated_labels,
        text_auto=True, 
        color_continuous_scale='Blues',
        aspect='auto' 
    )

    # Ajustes de diseño
    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Subcomunidad",
        xaxis=dict(side="bottom"), 
        height=500
    )
    
    return fig

def plot_bar_top_20e(df_keywords: pd.DataFrame, str_col) -> go.Figure:
    """
    Cuenta las palabras clave más frecuentes o los autores que más publican y genera un gráfico de barras horizontales.
    """
    str_nombres = {
        "palabrasclaves": {
            "ylabel": 'Palabras Clave',
            "title": 'Top 20 Palabras Clave más Frecuentes',
            "color_continuous_scale": 'turbo'
        },
        "autor": {
            "ylabel": 'Autores',
            "title": 'Top 20 Autores que más publican',
            "color_continuous_scale": 'plasma'
        }
    }
    
    # Obtener el top 20 de palabras clave (o de autores) y resetear índice para Plotly
    top_keywords = df_keywords[ str_col ].value_counts().head(20).reset_index()
    top_keywords.columns = [ str_nombres[str_col]["ylabel"] , 'Frecuencia']
    
    # Crear gráfico de barras horizontales interactivo
    fig = px.bar(
        top_keywords, 
        x='Frecuencia', 
        y= str_nombres[str_col]["ylabel"] , 
        orientation='h',
        color='Frecuencia',
        color_continuous_scale = str_nombres[str_col]["color_continuous_scale"],
        title= str_nombres[str_col]["title"]
    )
    
    # Ordenar el eje Y para que la barra más larga quede arriba
    fig.update_yaxes(
        showline=True,          # Mostrar línea del eje X
        linewidth=1,            # Grosor de la línea
        linecolor='black',      # Color de la línea del eje
        categoryorder='total ascending',
        tickmode='linear',  # Muestra una etiqueta por cada categoría sin omitir ninguna
        dtick=1
    )
    
    # Configuración explícita del Eje X (Frecuencia)
    fig.update_xaxes(
        showline=True,          # Mostrar línea del eje X
        linewidth=1,            # Grosor de la línea
        linecolor='black',      # Color de la línea del eje
        showgrid=True,          # Mostrar cuadrícula de fondo opcional
        gridcolor='LightGray'   # Color sutil para la cuadrícula
    )
    
    # Ocultar la barra de color
    fig.update_layout(coloraxis_showscale=False)
    
    return fig
