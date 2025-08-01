import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from services.utils import config
from database.models import model_base

load_dotenv()

DB_HOSTNAME: str = os.getenv("DB_HOSTNAME")
DB_PORT: str = os.getenv("DB_PORT")
DB_DATABASE: str = os.getenv("DB_DATABASE")
DB_USERNAME: str = os.getenv("DB_USERNAME")
DB_PASSWORD: str = os.getenv("DB_PASSWORD")

DATABASE_URL = f"mssql+pyodbc://{DB_USERNAME}:{DB_PASSWORD}@mssql:{DB_PORT}/{DB_DATABASE}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

print(DATABASE_URL)

database_engine = create_engine(
    DATABASE_URL,
    echo=True,  # False in production
    pool_pre_ping=True,
    pool_recycle=300
)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=database_engine)

# Create all tables
model_base.metadata.create_all(bind=database_engine)