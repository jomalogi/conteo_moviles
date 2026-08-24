import pandas as pd
from db_manager import init_db, delete_data_for_date, upload_dataframe
import datetime

# --- DICCIONARIOS Y LISTAS ---
company_map = {
    "CICSA COLOMBIA S.A.": "Tabasco OC",
    "TABASCO OC, LLC. SUCURSAL COLOMBIA": "Tabasco OC",
    "CONECTAR TV S.A.S.": "Conectar TV",
    "JESMAR HURTADO Y COMPANIA S. EN C.": "JESMAR",
    "ZENIX SAS": "ZENIX",
    "FENIX GROUP COMUNICACIONES S.A.S": "FENIX",
    "COMCEL SMART PHONE LTDA.": "SMARTPHONE",
    "PHONEMOVIL LTDA": "PHONEMOVIL",
    "COMCEL DAVIDMOVIL S.A.S": "DAVIDMOVIL",
    "COMCEL ISAMOVIL SAS": "ISAMOVIL",
    "PUNTO PRINCIPAL COMUNICACIONES S.A.S": "PUNTO PRINCIPAL",
    "COMCEL ARTECOM COMUNICACIONES S.A.S": "ARTECOM",
    "SOLUCIONES MOVILESRIO S.A.S.": "MOVILES RIO"
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
    "Mantenimientos Alto Valor": "Arreglos HFC",
    "Postventa DTH Postpago": "Posventa DTH",
    "Instalaciones Basica DTH Postpago": "Instalaciones DTH",
    "Mantenimiento DTH Postpago": "Arreglos DTH",
    "Traslado DTH Postpago": "Traslados DTH"
}

def process_and_upload(moviles_df, bases_operativas_df):
    try:
        # Inicializar DB
        init_db()
        
        # 1. Limpieza de moviles_dia
        moviles_df.columns = moviles_df.columns.str.strip()
        
        # Columnas requeridas
        col_compania = 'Compañia'
        if 'Compañía' in moviles_df.columns:
            col_compania = 'Compañía'
        elif 'Compaia' in moviles_df.columns:
            col_compania = 'Compaia'
            
        col_subtipo = 'Subtipo de la Orden de Trabajo'
        col_tecnico_id = 'External ID'
        col_tecnico_nombre = 'Técnico'
        if 'Tcnico' in moviles_df.columns:
            col_tecnico_nombre = 'Tcnico'
            
        col_ciudad = 'Ciudad'
        col_fecha = 'Fecha'
        col_estado = 'Estado'

        columnas_req = [col_compania, col_subtipo, col_tecnico_id, col_tecnico_nombre, col_ciudad, col_fecha, col_estado]
        
        faltantes = [c for c in columnas_req if c not in moviles_df.columns]
        if faltantes:
            return False, f"Faltan estas columnas en el archivo de móviles: {', '.join(faltantes)}"
            
        # Extraer fecha
        # Asumiendo que la fecha viene en la columna 'Fecha'
        fecha_val = moviles_df[col_fecha].dropna().iloc[0]
        
        # Comprobar si ya es un tipo fecha
        if isinstance(fecha_val, (pd.Timestamp, datetime.datetime, datetime.date)):
            if hasattr(fecha_val, 'date'):
                fecha_dt = fecha_val.date()
            else:
                fecha_dt = fecha_val
        else:
            fecha_str = str(fecha_val)
            try:
                # dayfirst=True asegura que 01/05/2026 se lea como 1 de Mayo y no 5 de Enero
                fecha_dt = pd.to_datetime(fecha_str, dayfirst=True).date()
            except:
                return False, f"No se pudo parsear la fecha: {fecha_str}"

        # Excluir supervisores si existe la columna
        col_tipo_act = 'Tipo de Actividad'
        if col_tipo_act in moviles_df.columns:
            moviles_df = moviles_df[~moviles_df[col_tipo_act].astype(str).str.strip().str.lower().isin(['supervisión', 'supervision'])]

        # 2. Aplicar mapeos y filtros
        df_base = moviles_df.copy()
        
        df_base['Compañía_Homologada'] = df_base[col_compania].astype(str).str.strip().map(company_map)
        df_base = df_base.dropna(subset=['Compañía_Homologada']).copy()
        # df_base = df_base.dropna(subset=['Compañía_Homologada']).copy()
        
        # Filtrar técnicos excluidos
        df_base = df_base[~df_base[col_tecnico_nombre].astype(str).str.strip().isin(lista_exclusion)]
        
        # Trabajo final
        df_base['Subtipo_Limpio'] = df_base[col_subtipo].astype(str).str.strip()
        df_base['Trabajo Final'] = df_base['Subtipo_Limpio'].map(mapping_subtipo).fillna("No es Tipo Trabajo")
        df_base = df_base[df_base['Trabajo Final'] != "No es Tipo Trabajo"]
        
        # Limpiar ID
        df_base = df_base.dropna(subset=[col_tecnico_id])
        df_base['ID_Limpio'] = df_base[col_tecnico_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df_base = df_base[df_base['ID_Limpio'].str.match(r'^\d+$') == True]
        df_base['tecnico_id'] = df_base['ID_Limpio']
        
        df_base['tecnico_nombre'] = df_base[col_tecnico_nombre].astype(str).str.strip()
        df_base['ciudad_limpia'] = df_base[col_ciudad].astype(str).str.strip().str.upper()

        # Calcular si el móvil NO inició ningún trabajo en todo el día
        df_base['Estado_Limpio'] = df_base[col_estado].astype(str).str.strip().str.lower()
        estados_iniciados = ['no completado', 'iniciado', 'completado']
        df_base['es_iniciado'] = df_base['Estado_Limpio'].isin(estados_iniciados)
        tecnicos_iniciados = df_base.groupby('ID_Limpio')['es_iniciado'].any().reset_index()
        tecnicos_iniciados.rename(columns={'es_iniciado': 'tiene_trabajo_iniciado'}, inplace=True)
        tecnicos_iniciados['sin_trabajo_iniciado'] = ~tecnicos_iniciados['tiene_trabajo_iniciado']
        df_base = pd.merge(df_base, tecnicos_iniciados, on='ID_Limpio', how='left')

        # 3. Limpieza de bases operativas
        bases_operativas_df.columns = bases_operativas_df.columns.str.strip()
        col_base_ciudad = 'Ciudad'
        col_base_aliado = 'Aliado Zonificado' if 'Aliado Zonificado' in bases_operativas_df.columns else 'Aliado Técnico'
        col_base_area = 'Area'
        col_base_operativa = 'Base Operativa'
        
        bo_faltantes = [c for c in [col_base_ciudad, col_base_aliado, col_base_area, col_base_operativa] if c not in bases_operativas_df.columns]
        if bo_faltantes:
            return False, f"Faltan estas columnas en bases operativas: {', '.join(bo_faltantes)}"

        bases_operativas_df['ciudad_limpia'] = bases_operativas_df[col_base_ciudad].astype(str).str.strip().str.upper()
        bases_operativas_df['Compañía_Homologada'] = bases_operativas_df[col_base_aliado].astype(str).str.strip()

        # 4. Cruzar bases operativas
        # Para evitar duplicados en el merge por si hay varias reglas de ciudad-aliado iguales, borramos duplicados
        bo_unicas = bases_operativas_df.drop_duplicates(subset=['ciudad_limpia', 'Compañía_Homologada'])
        
        df_final = pd.merge(
            df_base, 
            bo_unicas[['ciudad_limpia', 'Compañía_Homologada', col_base_area, col_base_operativa]],
            on=['ciudad_limpia', 'Compañía_Homologada'],
            how='left'
        )
        
        # Mapa de fallback para ciudades con Base Operativa sin asignar
        manual_bo_mapping = {
            "NEIVA CABLECENTRO": "Neiva",
            "UNION": "Tuluá",
            "POBLADO CAMPESTRE": "Palmira",
            "AMAIME": "Palmira",
            "VALLE": "Palmira",
            "BUGA": "Tuluá",
            "IBAGUE CABLECENTRO": "Ibagué",
            "CIUDAD DEL CAMPO": "Cali Norte"
        }
        
        # Aplicar el mapa a las vacías antes del fillna final
        df_final['bo_manual'] = df_final['ciudad_limpia'].map(manual_bo_mapping)
        df_final[col_base_operativa] = df_final[col_base_operativa].fillna(df_final['bo_manual'])
        
        # Rellenar vacios si no cruzó ni por Excel ni por diccionario
        df_final[col_base_area] = df_final[col_base_area].fillna("No asignado")
        df_final[col_base_operativa] = df_final[col_base_operativa].fillna("No asignado")

        # Seleccionar columnas para insertar a DB
        # DataFrame a MySQL:
        # fecha, tecnico_id, tecnico_nombre, compania, trabajo_final, ciudad, area, aliado_zonificado, base_operativa, sin_trabajo_iniciado
        df_to_db = pd.DataFrame()
        df_to_db['fecha'] = [fecha_dt] * len(df_final)
        df_to_db['tecnico_id'] = df_final['tecnico_id']
        df_to_db['tecnico_nombre'] = df_final['tecnico_nombre']
        df_to_db['compania'] = df_final['Compañía_Homologada'] # El aliado zonificado es el mismo
        df_to_db['trabajo_final'] = df_final['Trabajo Final']
        df_to_db['ciudad'] = df_final['ciudad_limpia']
        df_to_db['area'] = df_final[col_base_area]
        df_to_db['aliado_zonificado'] = df_final['Compañía_Homologada']
        df_to_db['base_operativa'] = df_final[col_base_operativa]
        df_to_db['sin_trabajo_iniciado'] = df_final['sin_trabajo_iniciado']

        # --- REGLA DTH: Forzar Base Operativa ---
        tipos_dth = ['Posventa DTH', 'Instalaciones DTH', 'Arreglos DTH', 'Traslados DTH']
        df_to_db.loc[df_to_db['trabajo_final'].isin(tipos_dth), 'base_operativa'] = 'Base DTH R3'
        
        # Obtener unicos (como en el app original que hace df_unicos por tecnico)
        # La regla original le da puntajes y luego hace drop_duplicates(subset=['tecnico_id'], keep='first')
        
        # Aplicar regla: Moda por defecto, pero si tiene Instalaciones FTTH o HFC, se priorizan
        jerarquia_inst = {
            "Instalaciones FTTH": 2000000,
            "Instalaciones HFC": 2000000,
            "Instalaciones DTH": 2000000
        }
        
        # Calcular el conteo original por técnico y tipo de trabajo
        freq_base = df_to_db.groupby(['tecnico_id', 'compania', 'trabajo_final', 'ciudad', 'area', 'aliado_zonificado', 'base_operativa', 'tecnico_nombre', 'fecha', 'sin_trabajo_iniciado']).size().reset_index(name='conteo')
        
        freq_base['Score'] = freq_base.apply(lambda r: r['conteo'] + jerarquia_inst.get(r['trabajo_final'], 0), axis=1)
        freq_base = freq_base.sort_values(by=['tecnico_id', 'Score'], ascending=[True, False])
        
        # Dejamos solo un registro por técnico por día
        df_unicos_db = freq_base.drop_duplicates(subset=['tecnico_id'], keep='first').copy()
        
        # Eliminar las columnas temporales Score y conteo
        df_unicos_db = df_unicos_db.drop(columns=['Score', 'conteo'])

        # HACK: Marcar en el nombre del tecnico si tuvo alguna orden Brownfield
        tecnicos_bf = df_to_db[df_to_db['trabajo_final'] == 'Brownfield']['tecnico_id'].unique()
        df_unicos_db.loc[df_unicos_db['tecnico_id'].isin(tecnicos_bf), 'tecnico_nombre'] += " [BF]"

        # 5. Insertar a la base de datos
        delete_data_for_date(fecha_dt)
        upload_dataframe(df_unicos_db)
        
        return True, f"Datos cargados exitosamente para la fecha {fecha_dt}. Se procesaron {len(df_unicos_db)} técnicos únicos."
        
    except Exception as e:
        return False, f"Ocurrió un error inesperado: {str(e)}"
