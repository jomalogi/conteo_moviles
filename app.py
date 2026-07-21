import streamlit as st
import pandas as pd
import plotly.express as px
from db_manager import get_historical_data
from upload_script import process_and_upload

def create_card(title, value, color):
    return f"""
    <div style="background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-top: 5px solid {color}; margin-bottom: 20px;">
        <p style="margin: 0; font-size: 0.85rem; color: #7f8c8d; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</p>
        <h2 style="margin: 5px 0 0 0; font-size: 2.2rem; font-weight: 800; color: {color};">{value}</h2>
    </div>
    """

# Configuración de la página
st.set_page_config(page_title="Tablero de Moviles Logueadas Regional Occidente", layout="wide")

st.title("📊 Tablero de Moviles Logueadas Regional Occidente")

tab1, tab2 = st.tabs(["📈 Dashboard Histórico", "📁 Cargar Nueva Base Diaria"])

with tab2:
    st.header("Carga de Bases Diarias")
    st.markdown("Sube el archivo `moviles_dia.xlsx` para agregar o actualizar los datos del día.")
    
    archivos_moviles = st.file_uploader("Cargar Bases de Móviles (.xlsx)", type=["xlsx", "xls"], key="moviles", accept_multiple_files=True)
    
    if st.button("Procesar y Cargar a Base de Datos"):
        if archivos_moviles:
            try:
                with st.spinner("Procesando y cargando a la base de datos..."):
                    # Leer el archivo estático localmente una sola vez
                    df_bases = pd.read_excel("bases_operativas.xlsx", engine='openpyxl')
                    
                    for f in archivos_moviles:
                        df_moviles = pd.read_excel(f, engine='openpyxl')
                        success, msg = process_and_upload(df_moviles, df_bases)
                        if success:
                            st.success(f"[{f.name}] {msg}")
                        else:
                            st.error(f"[{f.name}] {msg}")
            except Exception as e:
                st.error(f"Error general procesando los archivos: {e}")
        else:
            st.warning("Por favor, sube al menos un archivo de móviles para procesar.")

with tab1:
    st.header("Análisis Histórico")
    
    # Obtener datos de MySQL
    try:
        df_historico = get_historical_data()
    except Exception as e:
        st.error("No se pudo conectar a la base de datos MySQL. Revisa que el contenedor db esté corriendo.")
        df_historico = pd.DataFrame()
        
    if df_historico.empty:
        st.info("No hay datos históricos. Por favor carga una base diaria en la otra pestaña.")
    else:
        df_historico['fecha'] = pd.to_datetime(df_historico['fecha']).dt.date
        
        # Unificar problemas de codificación de tildes
        correcciones_tildes = {
            'IbaguÃ©': 'Ibagué',
            'TuluÃ¡': 'Tuluá'
        }
        df_historico['base_operativa'] = df_historico['base_operativa'].replace(correcciones_tildes)
        df_historico['ciudad'] = df_historico['ciudad'].replace(correcciones_tildes)
        
        # --- FILTROS LATERALES ---
        st.sidebar.header("Filtros")
        
        # Rango de fechas
        min_date = df_historico['fecha'].min()
        max_date = df_historico['fecha'].max()
        
        import datetime
        import calendar
        hoy = datetime.date.today()
        inicio_mes = hoy.replace(day=1)
        ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
        fin_mes = hoy.replace(day=ultimo_dia)
        
        # Asegurarse de que el valor por defecto esté dentro del rango permitido por min/max
        val_start = max(inicio_mes, min_date) if min_date else inicio_mes
        val_end = min(fin_mes, max_date) if max_date else fin_mes
        
        fechas_seleccionadas = st.sidebar.date_input(
            "Rango de Fechas", 
            value=(val_start, val_end),
            min_value=min_date,
            max_value=max_date
        )
        
        # Validación de las fechas seleccionadas
        if isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 2:
            start_date, end_date = fechas_seleccionadas
        elif isinstance(fechas_seleccionadas, tuple) and len(fechas_seleccionadas) == 1:
            start_date = end_date = fechas_seleccionadas[0]
        else:
            start_date = end_date = fechas_seleccionadas
            
        # Area
        list_areas = sorted(df_historico['area'].dropna().unique().tolist())
        area_sel = st.sidebar.multiselect("Área (dejar en blanco para todas)", list_areas, default=[])
        df_filtered = df_historico.copy()
        if area_sel:
            df_filtered = df_filtered[df_filtered['area'].isin(area_sel)]
            
        # Ciudad
        list_ciudades = sorted(df_filtered['ciudad'].dropna().unique().tolist())
        ciudad_sel = st.sidebar.multiselect("Ciudad (dejar en blanco para todas)", list_ciudades, default=[])
        if ciudad_sel:
            df_filtered = df_filtered[df_filtered['ciudad'].isin(ciudad_sel)]
            
        # Aliado Técnico
        list_aliados = sorted(df_filtered['aliado_zonificado'].dropna().unique().tolist())
        aliado_sel = st.sidebar.multiselect("Aliado Técnico (dejar en blanco para todos)", list_aliados, default=[])
        if aliado_sel:
            df_filtered = df_filtered[df_filtered['aliado_zonificado'].isin(aliado_sel)]
            
        # Base Operativa
        list_bo = sorted(df_filtered['base_operativa'].dropna().unique().tolist())
        bo_sel = st.sidebar.multiselect("Base Operativa (dejar en blanco para todas)", list_bo, default=[])
        if bo_sel:
            df_filtered = df_filtered[df_filtered['base_operativa'].isin(bo_sel)]

        # Tipo de Trabajo
        list_trabajos = sorted(df_filtered['trabajo_final'].dropna().unique().tolist())
        trabajo_sel = st.sidebar.multiselect("Tipo de Trabajo (dejar en blanco para todos)", list_trabajos, default=[])
        if trabajo_sel:
            df_filtered = df_filtered[df_filtered['trabajo_final'].isin(trabajo_sel)]

        # Aplicar filtro de fechas final
        df_filtered = df_filtered[
            (df_filtered['fecha'] >= start_date) & 
            (df_filtered['fecha'] <= end_date)
        ]

        # GARANTIZAR UNICIDAD: Un solo registro por Técnico (External ID) por Fecha
        df_filtered = df_filtered.drop_duplicates(subset=['fecha', 'tecnico_id'])

        import holidays

        # --- TARJETAS DE INDICADORES (KPIs) ---
        co_holidays = holidays.Colombia()
        
        # Obtener los días válidos en los datos filtrados (no domingos, no festivos)
        df_valid_days = df_filtered[
            df_filtered['fecha'].apply(lambda d: d.weekday() != 6 and d not in co_holidays)
        ]

        if not df_valid_days.empty:
            num_dias = df_valid_days['fecha'].nunique()
            if num_dias == 0:
                num_dias = 1
                
            # --- TARJETAS DE OBJETIVOS (PROMEDIOS DIARIOS) ---
            st.subheader("Promedio Móviles")
            df_trabajos_objetivos = df_valid_days[df_valid_days['trabajo_final'].isin(['Instalaciones FTTH', 'Instalaciones HFC', 'Brownfield'])]
            promedio_trabajos = len(df_trabajos_objetivos) / num_dias
            
            val_instalaciones = promedio_trabajos * 0.70
            val_brownfield = promedio_trabajos * 0.31
            val_traslados = promedio_trabajos * 0.10
            
            cols_obj = st.columns(3)
            with cols_obj[0]:
                st.markdown(create_card("Promedio Instalaciones", f"{val_instalaciones:.0f}", "#0284c7"), unsafe_allow_html=True)
            with cols_obj[1]:
                st.markdown(create_card("Promedio Brownfield", f"{val_brownfield:.0f}", "#7c3aed"), unsafe_allow_html=True)
            with cols_obj[2]:
                st.markdown(create_card("Promedio Traslados", f"{val_traslados:.0f}", "#0d9488"), unsafe_allow_html=True)
            
            st.divider()

            # Promedio regional total
            daily_total = df_valid_days.groupby('fecha')['tecnico_id'].nunique()
            avg_total = daily_total.mean()
            
            # Promedio por aliado
            daily_aliado = df_valid_days.groupby(['fecha', 'aliado_zonificado'])['tecnico_id'].nunique().reset_index()
            avg_aliado = daily_aliado.groupby('aliado_zonificado')['tecnico_id'].mean().to_dict()
            
            # Crear columnas para las tarjetas (1 para el total + 1 por cada aliado)
            num_cards = 1 + len(avg_aliado)
            cols = st.columns(num_cards)
            
            color_map = {
                "Tabasco OC": "#ABBD3A",
                "Conectar TV": "#FA960C"
            }
            palette = ["#2563eb", "#9333ea", "#0891b2", "#4f46e5", "#c026d3", "#0284c7"]
            
            with cols[0]:
                st.markdown(create_card("Regional Total (Días Hábiles)", f"{avg_total:.0f}", "#1e293b"), unsafe_allow_html=True)
            
            for idx, (aliado, avg) in enumerate(avg_aliado.items(), start=1):
                color = color_map.get(aliado, palette[(idx - 1) % len(palette)])
                with cols[idx]:
                    st.markdown(create_card(f"Promedio {aliado}", f"{avg:.0f}", color), unsafe_allow_html=True)
        else:
            st.info("No hay días hábiles (lunes a sábado, no festivos) en el rango seleccionado para calcular promedios.")
        
        st.divider()

        # --- GRÁFICO DE LÍNEAS (TENDENCIA) ---
        st.subheader("Tendencia de Móviles Totales por Fecha y Aliado")
        
        # Agrupado total
        df_tendencia_total = df_filtered.groupby('fecha').size().reset_index(name='Total')
        df_tendencia_total['Aliado'] = 'Total general'
        
        # Agrupado por aliado
        df_tendencia_aliado = df_filtered.groupby(['fecha', 'aliado_zonificado']).size().reset_index(name='Total')
        df_tendencia_aliado.rename(columns={'aliado_zonificado': 'Aliado'}, inplace=True)
        
        # Concatenar ambos
        df_tendencia_final = pd.concat([df_tendencia_total, df_tendencia_aliado])
        
        if not df_tendencia_final.empty:
            fig_line = px.line(
                df_tendencia_final, x='fecha', y='Total', color='Aliado',
                text='Total',
                markers=True, title="Histórico de Móviles Activos",
                labels={"fecha": "Fecha de Operación", "Total": "Cantidad de Móviles Activos"}
            )
            fig_line.update_traces(textposition="top center")
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No hay datos en la tendencia para graficar con estos filtros.")

        st.divider()

        # --- GRÁFICO DE LÍNEAS (TENDENCIA DE PROYECCIONES Y OTROS TRABAJOS) ---
        st.subheader("Tipos de Trabajo")
        
        proy_records = []
        
        # 1. Proyecciones (calculadas sobre la base de instalaciones)
        df_proy_daily = df_filtered[df_filtered['trabajo_final'].isin(['Instalaciones FTTH', 'Instalaciones HFC', 'Brownfield'])]
        if not df_proy_daily.empty:
            df_proy_grouped = df_proy_daily.groupby('fecha')['tecnico_id'].nunique().reset_index(name='total_base')
            for _, row in df_proy_grouped.iterrows():
                f = row['fecha']
                tb = row['total_base']
                proy_records.append({'fecha': f, 'Línea': 'Instalaciones (Proy)', 'Valor': round(tb * 0.70)})
                proy_records.append({'fecha': f, 'Línea': 'Brownfield (Proy)', 'Valor': round(tb * 0.31)})
                proy_records.append({'fecha': f, 'Línea': 'Traslados (Proy)', 'Valor': round(tb * 0.10)})
                
        # 2. Valores reales para los otros trabajos solicitados
        otros_trabajos = ['Arreglos HFC', 'Arreglos y Pvs FTTH', 'Posventa HFC', 'Desconexiones']
        df_otros_daily = df_filtered[df_filtered['trabajo_final'].str.strip().isin(otros_trabajos)]
        if not df_otros_daily.empty:
            df_otros_grouped = df_otros_daily.groupby(['fecha', 'trabajo_final'])['tecnico_id'].nunique().reset_index(name='Valor')
            for _, row in df_otros_grouped.iterrows():
                if str(row['trabajo_final']).strip() == 'Arreglos y Pvs FTTH':
                    arr_val = round(row['Valor'] * 0.82)
                    pos_val = row['Valor'] - arr_val
                    proy_records.append({'fecha': row['fecha'], 'Línea': 'Arreglos FTTH', 'Valor': arr_val})
                    proy_records.append({'fecha': row['fecha'], 'Línea': 'Posventa FTTH', 'Valor': pos_val})
                else:
                    proy_records.append({'fecha': row['fecha'], 'Línea': str(row['trabajo_final']).strip(), 'Valor': row['Valor']})
                
        df_tendencia_proy = pd.DataFrame(proy_records)
        
        if not df_tendencia_proy.empty:
            fig_line_proy = px.line(
                df_tendencia_proy, x='fecha', y='Valor', color='Línea',
                text='Valor',
                markers=True, title="Histórico por Tipos de Trabajo",
                labels={"fecha": "Fecha de Operación", "Valor": "Cantidad (Técnicos)"},
                color_discrete_map={
                    "Instalaciones (Proy)": "#0284c7", # Azul
                    "Brownfield (Proy)": "#7c3aed", # Púrpura
                    "Traslados (Proy)": "#0d9488", # Cerceta
                    "Arreglos HFC": "#e11d48", # Rosa oscuro
                    "Arreglos FTTH": "#f97316", # Naranja
                    "Posventa FTTH": "#fbbf24", # Amarillo
                    "Posventa HFC": "#4f46e5", # Índigo
                    "Desconexiones": "#64748b" # Gris Pizarra
                }
            )
            fig_line_proy.update_traces(textposition="top center")
            st.plotly_chart(fig_line_proy, use_container_width=True)
        else:
            st.info("No hay datos de proyecciones o trabajos para graficar con estos filtros.")

        col1, col2 = st.columns(2)
        
        # --- AGRUPADO POR BASE OPERATIVA ---
        with col1:
            st.subheader("Conteo por Base Operativa")
            df_bo = df_filtered.groupby(['base_operativa', 'ciudad', 'aliado_zonificado']).size().reset_index(name='conteo')
            df_bo = df_bo.sort_values(by='conteo', ascending=False)
            
            if not df_bo.empty:
                fig_bo = px.bar(
                    df_bo, x='base_operativa', y='conteo', color='aliado_zonificado',
                    hover_data=['ciudad'],
                    title="Móviles por Base Operativa",
                    text_auto=True
                )
                fig_bo.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bo, use_container_width=True)
            else:
                st.info("Sin datos para agrupar.")
                
        # --- AGRUPADO POR TIPO DE TRABAJO ---
        with col2:
            st.subheader("Conteo por Tipo de Trabajo")
            df_trabajo = df_filtered.groupby('trabajo_final').size().reset_index(name='conteo')
            
            row_arreglos_pie = df_trabajo[df_trabajo['trabajo_final'].astype(str).str.strip() == 'Arreglos y Pvs FTTH']
            if not row_arreglos_pie.empty:
                cantidad_base = row_arreglos_pie['conteo'].values[0]
                arreglos_ftth = round(cantidad_base * 0.82)
                posventa_ftth = cantidad_base - arreglos_ftth
                df_trabajo = df_trabajo[df_trabajo['trabajo_final'].astype(str).str.strip() != 'Arreglos y Pvs FTTH']
                new_rows = pd.DataFrame({'trabajo_final': ['Arreglos FTTH', 'Posventa FTTH'], 'conteo': [arreglos_ftth, posventa_ftth]})
                df_trabajo = pd.concat([df_trabajo, new_rows], ignore_index=True)
                
            df_trabajo = df_trabajo.sort_values(by='conteo', ascending=False)
            
            if not df_trabajo.empty:
                fig_trabajo = px.pie(
                    df_trabajo, names='trabajo_final', values='conteo',
                    title="Distribución por Tipo de Trabajo",
                    hole=0.4
                )
                st.plotly_chart(fig_trabajo, use_container_width=True)
            else:
                st.info("Sin datos para graficar.")

        # --- TABLAS DE RESUMEN ---
        col_tabla1, col_tabla2 = st.columns(2)
        
        with col_tabla1:
            st.subheader("Resumen por Tipo de Trabajo")
            df_resumen_trabajo = df_filtered.groupby('trabajo_final')['tecnico_id'].nunique().reset_index()
            df_resumen_trabajo.rename(columns={'trabajo_final': 'Tipo de Trabajo', 'tecnico_id': 'Cantidad'}, inplace=True)
            
            row_arreglos = df_resumen_trabajo[df_resumen_trabajo['Tipo de Trabajo'].astype(str).str.strip() == 'Arreglos y Pvs FTTH']
            if not row_arreglos.empty:
                cantidad_base = row_arreglos['Cantidad'].values[0]
                arreglos_ftth = round(cantidad_base * 0.82)
                posventa_ftth = cantidad_base - arreglos_ftth
                df_resumen_trabajo = df_resumen_trabajo[df_resumen_trabajo['Tipo de Trabajo'].astype(str).str.strip() != 'Arreglos y Pvs FTTH']
                new_rows = pd.DataFrame({'Tipo de Trabajo': ['Arreglos FTTH', 'Posventa FTTH'], 'Cantidad': [arreglos_ftth, posventa_ftth]})
                df_resumen_trabajo = pd.concat([df_resumen_trabajo, new_rows], ignore_index=True)
                
            df_resumen_trabajo = df_resumen_trabajo.sort_values(by='Cantidad', ascending=False).reset_index(drop=True)
            
            # Añadir fila de total
            total_cantidad = df_resumen_trabajo['Cantidad'].sum()
            df_resumen_trabajo.loc[len(df_resumen_trabajo)] = ['TOTAL', total_cantidad]
            
            st.dataframe(df_resumen_trabajo, hide_index=True)

        with col_tabla2:
            st.subheader("Móviles sin iniciar")
            if 'sin_trabajo_iniciado' in df_filtered.columns:
                # Filtrar donde sin_trabajo_iniciado es 1 o True
                df_sin_iniciar = df_filtered[df_filtered['sin_trabajo_iniciado'] == 1]
                if not df_sin_iniciar.empty:
                    df_resumen_aliado = df_sin_iniciar.groupby('aliado_zonificado')['tecnico_id'].nunique().reset_index()
                    df_resumen_aliado.rename(columns={'aliado_zonificado': 'Aliado', 'tecnico_id': 'Cantidad'}, inplace=True)
                    
                    df_resumen_aliado = df_resumen_aliado.sort_values(by='Cantidad', ascending=False).reset_index(drop=True)
                    total_sin_iniciar = df_resumen_aliado['Cantidad'].sum()
                    df_resumen_aliado.loc[len(df_resumen_aliado)] = ['TOTAL', total_sin_iniciar]
                    
                    st.dataframe(df_resumen_aliado, hide_index=True)
                else:
                    st.info("No hay móviles sin iniciar para los filtros seleccionados.")
            else:
                st.warning("La columna 'sin_trabajo_iniciado' no existe. Sube la base diaria de nuevo para recalcular.")