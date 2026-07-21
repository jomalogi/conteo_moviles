import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard de Despacho y Backlog", layout="wide")

st.title("📊 Dashboard de Técnicos por Compañía y Tipo de Trabajo")
st.markdown("Procesamiento con cálculo de moda (actividad más frecuente) y prioridad estricta para Instalaciones.")

# Carga de archivo
uploaded_file = st.file_uploader("Cargar Base de Datos (.xlsx)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        df.columns = df.columns.str.strip()
        
        # --- CONFIGURACIÓN DE COLUMNAS ---
        col_compania = 'Compañia'                       
        col_subtipo = 'Subtipo de la Orden de Trabajo'  
        col_tecnico_id = 'External ID'                  
        col_tecnico_nombre = 'Técnico'  # Columna donde están los nombres a excluir
        
        columnas_req = [col_compania, col_subtipo, col_tecnico_id, col_tecnico_nombre]
        faltantes = [c for c in columnas_req if c not in df.columns]
        if faltantes:
            st.error(f"Faltan estas columnas en el archivo para aplicar las nuevas reglas: {', '.join(faltantes)}")
            st.stop()

        # --- DICCIONARIOS Y LISTAS ---
        company_map = {
            "CICSA COLOMBIA S.A.": "Tabasco OC",
            "TABASCO OC, LLC. SUCURSAL COLOMBIA": "Tabasco OC",
            "CONECTAR TV S.A.S.": "Conectar TV"
        }
        
        lista_exclusion = [
            "ARRBUGA1", "ARRCALA1", "ARRCANA1", "ARRCCMA1", "ARRCEA1", "ARRCHKA1",
            "ARREFTTH", "ARRESPA1", "ARRFLEA1", "ARRFLRA1", "ARRIBAA1", "ARRMELA1",
            "ARRPAA1", "ARRPRA1", "ARRTULA1", "ARRYUA1", "BGFTINS", "BGFTMT",
            "BGFTTR", "CALCICPV", "DCC009", "DCE052", "DCE057", "DCE064", "DCE074",
            "DCE076", "DCE90", "DCE9111", "Delta 03", "DICOPASTO", "DOC020",
            "DOC023", "DOC033", "DOC035", "DOC039", "DOC045", "DOC047", "DOC091",
            "DOC096", "DOC097", "DOC0971", "DOC0981", "DOC100", "DOC101", "DOC102",
            "DOC103", "DOC104", "DOC107", "DOC108", "DOC109", "DOC110", "DOF033",
            "DOF065", "DOF204", "DOS012", "DOS063", "DOS072", "DR10", "DR11",
            "DR12", "DR13", "DR17", "DTN223", "DTN298", "DTN551", "DTN576",
            "DTN577", "DTO573", "DTO574", "DTY001", "DXRXBUGA1", "DXRXCA1",
            "DXRXCANA1", "DXRXCCMA1", "DXRXCEA1", "DXRXCHKA1", "DXRXESPA1",
            "DXRXFLEA1", "DXRXFLRA1", "DXRXIBAA1", "DXRXMELA1", "DXRXPAA1",
            "DXRXPRA1", "DXRXTULA1", "DXRXYUA1", "DXYRX1", "FHPY1", "FTHIPI",
            "FTTH001", "FTTHANDA1", "FTTHBUGA1", "FTTHCA1", "FTTHCAIA1",
            "FTTHCANA1", "FTTHCCMNA1", "FTTHCEA1", "FTTHCGOA1", "FTTHCHKNA1",
            "ftthCI49", "FTTHESPNA1", "FTTHFLENA1", "FTTHFLRA1", "FTTHGUOA1",
            "FTTHIBANA1", "FTTHMELNA1", "FTTHPAA1", "FTTHPRA1", "FTTHPT1",
            "FTTHROLA1", "FTTHSEVA1", "FTTHTULNA1", "FTTHUNIA1", "FTTHYUA1",
            "FTTHZRZA1", "FTTXCAL1", "FTTXIBA1", "FTTXPAS1", "FTTXPOP1",
            "GAR001", "Instalaciones y Traslados", "INSTFTHJA", "INSTFTTH",
            "INSTRBUGA1", "INSTRCA1", "INSTRCANA1", "INSTRCCMA1", "INSTRCEA1",
            "INSTRCHKA1", "INSTRESPA1", "INSTRFLEA1", "INSTRFLRA1", "INSTRIBAA1",
            "INSTRMELA1", "INSTRPAA1", "INSTRPRA1", "INSTRTULA1", "INSTRYUA1",
            "INYT1", "IYT1", "M23989", "Mantenimiento1", "Mantenimiento2",
            "MANY2", "MASVCH", "ME_TELCOS_ANTIOQUIA_1", "MPP1", "MTOFTHJA",
            "P23990", "Pitalito1", "POS1917", "PVSBUGA1", "PVSCA1", "PVSCANA1",
            "PVSCCMA1", "PVSCEA1", "PVSCHKA1", "PVSESPA1", "PVSFLEA1", "PVSFLRA1",
            "PVSIBAA1", "PVSMELA1", "PVSPAA1", "PVSPRA1", "PVSTULA1", "PVSYUA1",
            "PYM709", "PYMCI09", "PYMCI10", "PYMCI20", "PYMCI23", "PYMCI37",
            "PYMCI50", "REO339", "Z2Cal", "Z2FTTX", "Z2INSTPY", "Z2MTTOPY",
            "Z3LY", "ZA1AND001", "ZA1BUG001", "ZA1CAI001", "ZA1CAL01", "ZA1CAN001",
            "ZA1CCM001", "ZA1CE001", "ZA1CGO001", "ZA1CHK001", "ZA1ESP001",
            "ZA1FLE001", "ZA1FLR001", "ZA1GUO001", "ZA1IBA001", "ZA1MEL001",
            "ZA1PA001", "ZA1PR001", "ZA1ROL001", "ZA1SEV001", "ZA1TUL001",
            "ZA1UNI001", "ZA1Y001", "ZA1ZRZ001", "DOC019"
        ]

        mapping_subtipo = {
            "Almuerzo": "No es Tipo Trabajo",
            "Otros": "No es Tipo Trabajo",
            "Arreglos": "Arreglos HFC",
            "Actividades de Almacen": "No es Tipo Trabajo",
            "Orden Especial Masivo FTTH": "Instalaciones FTTH",
            "Postventa FTTX": "Arreglos y Pvs FTTH",
            "Traslado Pymes": "Instalaciones HFC",
            "Cambio Tecnologia TV": "Posventa HFC",
            "Capacitacion": "No es Tipo Trabajo",
            "Llegada Tarde": "No es Tipo Trabajo",
            "VENTAS TECNICO": "Posventa HFC",
            "Vehiculo con Fallas": "No es Tipo Trabajo",
            "Recursos Humanos": "No es Tipo Trabajo",
            "Encuesta Técnicos": "No es Tipo Trabajo",
            "Permiso": "No es Tipo Trabajo",
            "Actualización de datos": "No es Tipo Trabajo",
            "ENTREGA DE SERVICIOS FO": "Instalaciones FTTH",
            "Orden Especial": "Instalaciones FTTH",
            "Arreglo Bidireccional": "Arreglos HFC",
            "Arreglo Pymes": "Arreglos HFC",
            "Instalacion Empaquetada Bi": "Instalaciones HFC",
            "PostVenta Bi": "Posventa HFC",
            "Blindaje": "Posventa HFC",
            "Instalacion Basica Bi": "Instalaciones HFC",
            "Instalacion FTTH_": "Instalaciones FTTH",
            "Mantenimiento FTTH": "Arreglos y Pvs FTTH",
            "Visita Mejoramiento": "Arreglos HFC",
            "Desconexiones x Carta Movimiento Bi": "Desconexiones",
            "Postventa FTTH": "Arreglos y Pvs FTTH",
            "BROWNFIELD": "Brownfield",
            "Traslado FTTH": "Instalaciones FTTH",
            "Brownfield Flash": "Brownfield",
            "Instalacion FWA": "Instalaciones FTTH",
            "Traslado Bi": "Instalaciones HFC",
            "Instalacion Cableada Bi": "Instalaciones HFC",
            "Arreglos FTTX": "Arreglos y Pvs FTTH",
            "Instalacion Pymes": "Instalaciones HFC",
            "Instalaciones FTTX": "Instalaciones FTTH",
            "Traslados FTTX": "Instalaciones FTTH",
            "Mantenimiento FWA": "Arreglos y Pvs FTTH",
            "Postventa Pymes": "Posventa HFC",
            "Brownfield Pymes": "Brownfield",
            "Reconexion Bi": "No es Tipo Trabajo",
            "Ventas Tecnico FTTH": "Arreglos y Pvs FTTH",
            "Desconexion x Servicio Bi": "Desconexiones",
            "Ventas Tecnico BI": "Posventa HFC",
            "Traslado Mintic FTTH": "Instalaciones FTTH",
            "Traslados MINTIC": "Instalaciones HFC",
            "Orden Especial Masivo HFC": "Posventa HFC",
            "Cambio de equipos FWA": "Arreglos y Pvs FTTH",
            "Blindaje Pymes": "Posventa HFC",
            "FO Visita Tecnica VOC": "No es Tipo Trabajo",
            "Orden Especial Pymes HFC": "Instalaciones HFC",
            "Arreglo Especial Masivo FTTH": "Arreglos y Pvs FTTH",
            "Orden Especial Migracion Corporativo": "Brownfield",
            "Orden Especial Pymes FTTX": "Instalaciones FTTH",
            "Mantenimientos Alto Valor": "Arreglos HFC"
        }

        # --- LIMPIEZA INICIAL ---
        df['Compañía_Homologada'] = df[col_compania].astype(str).str.strip().map(company_map)
        df_base = df.dropna(subset=['Compañía_Homologada']).copy()
        
        # Filtrar nombres de Técnicos excluidos
        df_base = df_base[~df_base[col_tecnico_nombre].astype(str).str.strip().isin(lista_exclusion)]
        
        # Mapeo de Subtipo a Trabajo Final
        df_base['Subtipo_Limpio'] = df_base[col_subtipo].astype(str).str.strip()
        df_base['Trabajo Final'] = df_base['Subtipo_Limpio'].map(mapping_subtipo).fillna("No es Tipo Trabajo")
        
        # Excluir los "No es Tipo Trabajo"
        df_base = df_base[df_base['Trabajo Final'] != "No es Tipo Trabajo"]
        
        # Validar ID numérico
        df_base = df_base.dropna(subset=[col_tecnico_id])
        df_base['ID_Limpio'] = df_base[col_tecnico_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df_base = df_base[df_base['ID_Limpio'].str.match(r'^\d+$') == True]
        df_base[col_tecnico_id] = df_base['ID_Limpio']

        # =====================================================================
        # --- LÓGICA EXCEL: MODA CON PRIORIDAD ABSOLUTA EN INSTALACIONES ---
        # =====================================================================
        # 1. Contar cuántas OTs tiene cada técnico de cada tipo (Moda Base)
        freq = df_base.groupby([col_tecnico_id, 'Compañía_Homologada', 'Trabajo Final']).size().reset_index(name='conteo')
        
        # 2. Inyectar prioridad si es Instalación o Brownfield (Anula el conteo y fuerza la categoría)
        jerarquia_inst = {
            "Instalaciones FTTH": 3000000,
            "Instalaciones HFC": 2000000,
            "Brownfield": 1000000
        }
        
        def calculate_score(row):
            score_base = row['conteo']
            boost = jerarquia_inst.get(row['Trabajo Final'], 0)
            return score_base + boost

        freq['Score'] = freq.apply(calculate_score, axis=1)
        
        # 3. Ordenar por Puntaje de mayor a menor y dejar solo el ganador por Técnico
        freq = freq.sort_values(by=[col_tecnico_id, 'Score'], ascending=[True, False])
        df_unicos = freq.drop_duplicates(subset=[col_tecnico_id], keep='first').copy()
        # =====================================================================

        # --- FILTRO INTERACTIVO ---
        list_companias = ["Todas"] + sorted(df_unicos['Compañía_Homologada'].unique().tolist())
        compania_sel = st.sidebar.selectbox("Seleccionar Compañía", list_companias)
        
        if compania_sel != "Todas":
            df_unicos = df_unicos[df_unicos['Compañía_Homologada'] == compania_sel]
        
        # --- CÁLCULO DE MÉTRICAS ---
        total_hfc = df_unicos[df_unicos['Trabajo Final'] == "Instalaciones HFC"].shape[0]
        cant_ftth = df_unicos[df_unicos['Trabajo Final'] == "Instalaciones FTTH"].shape[0]
        cant_brownfield = df_unicos[df_unicos['Trabajo Final'] == "Brownfield"].shape[0]
        
        # Los "Traslados FTTH" ya se agruparon automáticamente en Instalaciones FTTH según el nuevo mapeo
        total_ftth_formula = (cant_ftth + cant_brownfield) * 0.63

        # --- INTERFAZ ---
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Instalaciones HFC", f"{total_hfc}")
        with c2:
            st.metric("Instalaciones FTTH (Fórmula 63%)", f"{total_ftth_formula:.2f}")
        with c3:
            total_global = df_unicos.shape[0]
            st.metric("Total Técnicos Únicos Activos", total_global)

        # --- GRÁFICA ---
        resumen = df_unicos.groupby(['Trabajo Final'])[col_tecnico_id].count().reset_index()
        resumen.rename(columns={col_tecnico_id: 'Cantidad de Técnicos'}, inplace=True)
        
        if not resumen.empty:
            resumen = resumen.sort_values(by='Cantidad de Técnicos', ascending=False)
            fig = px.bar(
                resumen, 
                x='Trabajo Final', 
                y='Cantidad de Técnicos',
                text_auto=True,
                title=f"Distribución Final - {compania_sel}",
                color='Trabajo Final'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos para mostrar con los filtros actuales.")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
        #ejecutar desde la raiz streamlit run app.py