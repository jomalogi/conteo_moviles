import os
import pandas as pd
from sqlalchemy import create_engine, text

def get_engine():
    # Obtener credenciales de variables de entorno o usar valores por defecto para pruebas locales
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "root")
    db_name = os.getenv("DB_NAME", "conteo_moviles")
    db_port = os.getenv("DB_PORT", "3312")

    engine_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(engine_url)
    return engine

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe."""
    engine = get_engine()
    
    # Crear la tabla historico_moviles
    create_table_query = """
    CREATE TABLE IF NOT EXISTS historico_moviles (
        id INT AUTO_INCREMENT PRIMARY KEY,
        fecha DATE,
        tecnico_id VARCHAR(100),
        tecnico_nombre VARCHAR(255),
        compania VARCHAR(255),
        trabajo_final VARCHAR(255),
        ciudad VARCHAR(255),
        area VARCHAR(255),
        aliado_zonificado VARCHAR(255),
        base_operativa VARCHAR(255),
        sin_trabajo_iniciado BOOLEAN DEFAULT FALSE
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_table_query))

def delete_data_for_date(fecha):
    """Elimina los datos para una fecha específica para poder reemplazarlos."""
    engine = get_engine()
    query = text("DELETE FROM historico_moviles WHERE fecha = :fecha")
    with engine.begin() as conn:
        conn.execute(query, {"fecha": fecha})

def upload_dataframe(df):
    """Sube el dataframe a la tabla historico_moviles."""
    engine = get_engine()
    df.to_sql(name='historico_moviles', con=engine, if_exists='append', index=False)

def get_historical_data():
    """Obtiene todos los datos históricos de la base de datos."""
    engine = get_engine()
    query = "SELECT * FROM historico_moviles"
    try:
        df = pd.read_sql(query, con=engine)
        return df
    except Exception as e:
        print(f"Error reading from database: {e}")
        return pd.DataFrame()
