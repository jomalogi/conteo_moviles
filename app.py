import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

tab1, tab2, tab3 = st.tabs(["📈 Dashboard Histórico", "📁 Cargar Nueva Base Diaria", "👥 Análisis de Rotación"])

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
                    
                    import pandas as pd
                    # 1. Unir todos los Excels en uno solo
                    df_list = []
                    for f in archivos_moviles:
                        df_list.append(pd.read_excel(f, engine='openpyxl'))
                    df_all = pd.concat(df_list, ignore_index=True)
                    
                    # 2. Buscar la columna de fecha
                    col_fecha = 'Fecha'
                    
                    if col_fecha in df_all.columns:
                        # Convertir a fecha real para agrupar
                        df_all[col_fecha] = pd.to_datetime(df_all[col_fecha], dayfirst=True)
                        
                        # 3. Procesar día por día (FTTH y DTH mezclados juntos)
                        for fecha_dt, grupo in df_all.groupby(df_all[col_fecha].dt.date):
                            success, msg = process_and_upload(grupo.copy(), df_bases)
                            if success:
                                st.success(f"Fecha {fecha_dt}: {msg}")
                            else:
                                st.error(f"Error en {fecha_dt}: {msg}")
                    else:
                        st.error("Ninguno de los archivos tiene la columna 'Fecha'.")
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

        # --- SEPARAR DTH ---
        tipos_dth = ['Posventa DTH', 'Instalaciones DTH', 'Arreglos DTH', 'Traslados DTH']
        df_filtered_dth = df_filtered[df_filtered['trabajo_final'].isin(tipos_dth)].copy()
        df_filtered = df_filtered[~df_filtered['trabajo_final'].isin(tipos_dth)]

        # --- GUARDAR COPIA ANTES DE UNIFICAR PARA CONTAR BROWNFIELD REAL ---
        df_filtered_raw = df_filtered.copy()

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
            
            # --- NUEVA TARJETA: MOV CON BF ---
            df_raw_valid = df_filtered_raw[
                df_filtered_raw['fecha'].apply(lambda d: d.weekday() != 6 and d not in co_holidays)
            ]
            
            df_bf = df_raw_valid[df_raw_valid['tecnico_nombre'].astype(str).str.contains(r'\[BF\]', na=False)]
            total_mov_bf = df_bf.drop_duplicates(subset=['fecha', 'tecnico_id']).shape[0]
            
            cols_obj = st.columns(4)
            with cols_obj[0]:
                st.markdown(create_card("Promedio Instalaciones", f"{val_instalaciones:.0f}", "#0284c7"), unsafe_allow_html=True)
            with cols_obj[1]:
                st.markdown(create_card("Promedio Brownfield", f"{val_brownfield:.0f}", "#7c3aed"), unsafe_allow_html=True)
            with cols_obj[2]:
                st.markdown(create_card("MOV CON BF", f"{total_mov_bf}", "#f59e0b"), unsafe_allow_html=True)
            with cols_obj[3]:
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
        
        # Diccionario de Móviles Sugeridas por Base Operativa
        sugeridas_dict = {
            "Cali Norte": 141,
            "Cali Sur": 222,
            "Espinal": 15,
            "Florencia": 13,
            "Huila": 5,
            "Ibagué": 72,
            "Neiva": 80,
            "Palmira": 51,
            "Pasto": 43,
            "Popayán": 43,
            "Tuluá": 54
        }
        
        # Calcular el total de móviles sugeridas
        # Sumamos solo las bases que están presentes en los datos filtrados
        bases_presentes = df_filtered['base_operativa'].dropna().unique()
        total_sugeridas = sum([sugeridas_dict.get(bo, 0) for bo in bases_presentes])
        
        # Agrupado total
        df_tendencia_total = df_filtered.groupby('fecha').size().reset_index(name='Total')
        df_tendencia_total['Aliado'] = 'Total general'
        
        if total_sugeridas > 0:
            df_tendencia_total['Cumplimiento'] = (df_tendencia_total['Total'] / total_sugeridas * 100).round(1).astype(str) + '%'
        else:
            df_tendencia_total['Cumplimiento'] = ''
            
        # Agrupado por aliado
        df_tendencia_aliado = df_filtered.groupby(['fecha', 'aliado_zonificado']).size().reset_index(name='Total')
        df_tendencia_aliado.rename(columns={'aliado_zonificado': 'Aliado'}, inplace=True)
        df_tendencia_aliado['Cumplimiento'] = ''
        
        # Línea de Sugeridas
        df_sugeridas = df_tendencia_total[['fecha']].copy()
        df_sugeridas['Total'] = total_sugeridas
        df_sugeridas['Aliado'] = 'Móviles Sugeridas'
        df_sugeridas['Cumplimiento'] = ''
        
        # Concatenar ambos
        df_tendencia_final = pd.concat([df_tendencia_total, df_tendencia_aliado, df_sugeridas])
        
        if not df_tendencia_final.empty:
            # Añadir título dinámico
            titulo_grafico = "Histórico de Móviles Activos"
            if total_sugeridas > 0 and not df_tendencia_total.empty:
                ultimo_total = df_tendencia_total.iloc[-1]['Total']
                ultimo_porcentaje = (ultimo_total / total_sugeridas * 100)
                titulo_grafico += f" (Meta Sugerida: {total_sugeridas} | Último Cumplimiento: {ultimo_porcentaje:.1f}%)"

            # Crear figura base con plotly express
            fig_line = px.line(
                df_tendencia_final, x='fecha', y='Total', color='Aliado',
                text='Total',
                markers=True, title=titulo_grafico,
                labels={"fecha": "Fecha de Operación", "Total": "Cantidad de Móviles"},
                hover_data={"Cumplimiento": True}
            )
            fig_line.update_traces(textposition="top center")
            
            # Hacer que la línea de sugeridas sea punteada para distinguirla visualmente
            for idx, trace in enumerate(fig_line.data):
                if trace.name == 'Móviles Sugeridas':
                    fig_line.data[idx].line.dash = 'dot'
                    fig_line.data[idx].line.color = '#ef4444' # Rojo claro
                    
            # Crear figura con subplots para doble eje Y
            fig_final = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Añadir las trazas de px.line a la nueva figura
            for trace in fig_line.data:
                fig_final.add_trace(trace, secondary_y=False)
                
            # Añadir línea de % Cumplimiento
            if total_sugeridas > 0 and not df_tendencia_total.empty:
                porcentaje_num = (df_tendencia_total['Total'] / total_sugeridas * 100).round(1)
                fig_final.add_trace(
                    go.Scatter(
                        x=df_tendencia_total['fecha'], 
                        y=porcentaje_num, 
                        name='% Cumplimiento', 
                        mode='lines+markers+text',
                        text=porcentaje_num.astype(str) + '%',
                        textposition="bottom right",
                        line=dict(color='#f59e0b', width=2, dash='dash'), # Naranja oscuro
                        hovertemplate='<b>%{x}</b><br>Cumplimiento: %{y}%<extra></extra>'
                    ),
                    secondary_y=True
                )
                
            # Actualizar diseño
            fig_final.update_layout(
                title=fig_line.layout.title,
                xaxis_title="Fecha de Operación",
                legend_title_text='Aliado / Métrica'
            )
            fig_final.update_yaxes(title_text="Cantidad de Móviles", secondary_y=False)
            
            if total_sugeridas > 0 and not df_tendencia_total.empty:
                max_pct = max(110.0, porcentaje_num.max() + 10.0)
                fig_final.update_yaxes(title_text="% de Cumplimiento", secondary_y=True, range=[0, max_pct])
            else:
                fig_final.update_yaxes(title_text="% de Cumplimiento", secondary_y=True, range=[0, 100])
                
            st.plotly_chart(fig_final, use_container_width=True)
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

        # --- SECCIÓN OPERACIÓN DTH ---
        st.divider()
        st.header("📡 Operación DTH")
        
        df_dth_unicos = df_filtered_dth.drop_duplicates(subset=['fecha', 'tecnico_id'])
        
        col_dth1, col_dth2, col_dth3 = st.columns([2, 1, 1])
        
        with col_dth1:
            st.subheader("Histórico DTH por Fecha")
            if not df_dth_unicos.empty:
                df_tendencia_dth = df_dth_unicos.groupby(['fecha', 'trabajo_final']).size().reset_index(name='Valor')
                
                # Importar colores extra si es necesario
                import plotly.express as px
                fig_dth = px.line(
                    df_tendencia_dth, x='fecha', y='Valor', color='trabajo_final',
                    text='Valor', markers=True,
                    labels={"fecha": "Fecha", "Valor": "Cantidad (Técnicos)", "trabajo_final": "Tipo DTH"},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                fig_dth.update_traces(textposition="top center")
                st.plotly_chart(fig_dth, use_container_width=True)
            else:
                st.info("No hay datos de DTH para graficar en este periodo.")
                
        with col_dth2:
            st.subheader("Resumen DTH")
            if not df_dth_unicos.empty:
                df_resumen_dth = df_dth_unicos.groupby('trabajo_final')['tecnico_id'].nunique().reset_index()
                df_resumen_dth.rename(columns={'trabajo_final': 'Tipo DTH', 'tecnico_id': 'Cantidad'}, inplace=True)
                df_resumen_dth = df_resumen_dth.sort_values(by='Cantidad', ascending=False).reset_index(drop=True)
                
                total_dth = df_resumen_dth['Cantidad'].sum()
                df_resumen_dth.loc[len(df_resumen_dth)] = ['TOTAL DTH', total_dth]
                st.dataframe(df_resumen_dth, hide_index=True)
            else:
                st.info("Sin datos de DTH.")
                
        with col_dth3:
            st.subheader("DTH por Aliado")
            if not df_dth_unicos.empty:
                df_aliado_dth = df_dth_unicos.groupby('aliado_zonificado')['tecnico_id'].nunique().reset_index()
                df_aliado_dth.rename(columns={'aliado_zonificado': 'Aliado', 'tecnico_id': 'Cantidad'}, inplace=True)
                df_aliado_dth = df_aliado_dth.sort_values(by='Cantidad', ascending=False).reset_index(drop=True)
                
                total_aliados = df_aliado_dth['Cantidad'].sum()
                df_aliado_dth.loc[len(df_aliado_dth)] = ['TOTAL', total_aliados]
                st.dataframe(df_aliado_dth, hide_index=True)
            else:
                st.info("Sin datos de Aliados DTH.")

        

# --- PESTAÑA 3: ROTACIÓN ---
with tab3:
    st.header("👥 Análisis de Rotación de Técnicos (Proxy Turnover)")
    st.markdown("Este módulo mide la retención de los Aliados asumiendo que un técnico que **no ha registrado actividad en los últimos 30 días** ha causado baja (renuncia/despido).")
    
    if df_historico.empty:
        st.warning("No hay datos históricos para calcular la rotación.")
    else:
        import pandas as pd
        # Fecha de análisis (el día más reciente con datos en la BD)
        fecha_fin_rot = df_historico['fecha'].max()
        fecha_inicio_activos = fecha_fin_rot - pd.Timedelta(days=30)
        
        st.info(f"**Periodo de Plantilla Activa:** {fecha_inicio_activos.strftime('%Y-%m-%d')} al {fecha_fin_rot.strftime('%Y-%m-%d')}")
        
        # Obtener el último Aliado y Base Operativa conocido para cada técnico (en caso de que hayan rotado internamente)
        df_sorted = df_historico.sort_values('fecha')
        df_latest_info = df_sorted.drop_duplicates(subset=['tecnico_id'], keep='last')[['tecnico_id', 'tecnico_nombre', 'aliado_zonificado', 'base_operativa', 'fecha']]
        df_latest_info = df_latest_info.rename(columns={'fecha': 'ultima_fecha_actividad'})
        
        # 1. Técnicos Activos (cualquier actividad en los últimos 30 días)
        activos_30d = df_historico[df_historico['fecha'] > fecha_inicio_activos]
        tecnicos_activos_ids = activos_30d['tecnico_id'].unique()
        
        # 2. Técnicos Históricos (existían antes de la ventana de 30 días)
        historico_previo = df_historico[df_historico['fecha'] <= fecha_inicio_activos]
        tecnicos_previos_ids = historico_previo['tecnico_id'].unique()
        
        # 3. Detectar Bajas (Estaban en la historia pero NO en los activos recientes)
        bajas_ids = set(tecnicos_previos_ids) - set(tecnicos_activos_ids)
        
        df_activos = df_latest_info[df_latest_info['tecnico_id'].isin(tecnicos_activos_ids)].copy()
        df_bajas = df_latest_info[df_latest_info['tecnico_id'].isin(bajas_ids)].copy()
        
        # --- APLICAR FILTROS LATERALES ---
        if 'aliado_sel' in dir() and aliado_sel:
            df_activos = df_activos[df_activos['aliado_zonificado'].isin(aliado_sel)]
            df_bajas = df_bajas[df_bajas['aliado_zonificado'].isin(aliado_sel)]
        if 'bo_sel' in dir() and bo_sel:
            df_activos = df_activos[df_activos['base_operativa'].isin(bo_sel)]
            df_bajas = df_bajas[df_bajas['base_operativa'].isin(bo_sel)]
            
        # Actualizar contadores para las tarjetas superiores
        tecnicos_activos_ids = df_activos['tecnico_id'].unique()
        bajas_ids = df_bajas['tecnico_id'].unique()
        
        # --- MÉTRICAS GLOBALES SUPERIORES ---
        col_m1, col_m2, col_m3 = st.columns(3)
        total_activos = len(tecnicos_activos_ids)
        total_bajas = len(bajas_ids)
        rotacion_global = (total_bajas / total_activos * 100) if total_activos > 0 else 0
        
        col_m1.metric("Plantilla Activa", f"{total_activos} técnicos", help="Técnicos únicos que hicieron trabajos en los últimos 30 días")
        col_m2.metric("Bajas Detectadas", f"{total_bajas} técnicos", help="No registran actividad en los últimos 30 días", delta_color="inverse")
        col_m3.metric("Rotación Global", f"{rotacion_global:.1f}%")
        
        st.divider()
        
        # --- TABLA DE ROTACIÓN POR ALIADO Y BASE ---
        st.subheader("Rotación por Aliado y Base Operativa")
        
        agrupado_activos = df_activos.groupby(['aliado_zonificado', 'base_operativa']).size().reset_index(name='Plantilla Activa')
        agrupado_bajas = df_bajas.groupby(['aliado_zonificado', 'base_operativa']).size().reset_index(name='Bajas')
        
        df_rotacion = pd.merge(agrupado_activos, agrupado_bajas, on=['aliado_zonificado', 'base_operativa'], how='outer').fillna(0)
        df_rotacion['Plantilla Activa'] = df_rotacion['Plantilla Activa'].astype(int)
        df_rotacion['Bajas'] = df_rotacion['Bajas'].astype(int)
        df_rotacion['% Rotación'] = (df_rotacion['Bajas'] / df_rotacion['Plantilla Activa'] * 100).fillna(0)
        df_rotacion['% Rotación'] = df_rotacion['% Rotación'].replace([float('inf')], 100.0).round(1)
        
        # Ordenar para que los de mayor rotación salgan arriba
        df_rotacion = df_rotacion.sort_values(by='% Rotación', ascending=False).reset_index(drop=True)
        
        # Mostrar tabla con mapa de calor (rojo = mucha rotación)
        df_rotacion_fmt = df_rotacion.copy()
        df_rotacion_fmt['% Rotación'] = df_rotacion_fmt['% Rotación'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_rotacion_fmt, hide_index=True, use_container_width=True)
        
        st.divider()
        
        # --- LISTA DETALLADA DE BAJAS ---
        st.subheader("📋 Lista Negra: Detalle de Técnicos Perdidos")
        st.markdown("Identifica a los técnicos exactos que abandonaron la operación y envíaselos a los Aliados para pedir explicaciones.")
        
        if not df_bajas.empty:
            df_bajas_mostrar = df_bajas.sort_values(by='ultima_fecha_actividad', ascending=False)
            df_bajas_mostrar['ultima_fecha_actividad'] = pd.to_datetime(df_bajas_mostrar['ultima_fecha_actividad']).dt.strftime('%Y-%m-%d')
            
            col_f1, col_f2 = st.columns([1, 2])
            with col_f1:
                filtro_aliado = st.selectbox("Filtrar Bajas por Aliado", ["Todos"] + sorted(df_bajas_mostrar['aliado_zonificado'].dropna().unique().tolist()))
                if filtro_aliado != "Todos":
                    df_bajas_mostrar = df_bajas_mostrar[df_bajas_mostrar['aliado_zonificado'] == filtro_aliado]
                
            st.dataframe(
                df_bajas_mostrar[['tecnico_id', 'tecnico_nombre', 'aliado_zonificado', 'base_operativa', 'ultima_fecha_actividad']].rename(
                    columns={
                        'tecnico_id': 'ID Técnico',
                        'tecnico_nombre': 'Nombre del Técnico',
                        'aliado_zonificado': 'Aliado',
                        'base_operativa': 'Base Operativa',
                        'ultima_fecha_actividad': 'Último día trabajado'
                    }
                ),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.success("¡Excelente! No se detectaron bajas.")
