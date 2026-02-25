import os
import mysql.connector
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME')
}

# Construcción de URL de conexión para SQLAlchemy
SQLALCHEMY_DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
)

# Configuración del motor SQLAlchemy
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    pool_recycle=3600,   # Reciclar conexiones cada hora
    echo=False           # No mostrar SQL en producción
)

# Configuración de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base declarativa para modelos ORM
Base = declarative_base()


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # from app.models import artist, song_metadata, song_files, song_backup, file_index, user
    Base.metadata.create_all(bind=engine)