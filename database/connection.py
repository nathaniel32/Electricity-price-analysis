from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from services.utils import config
from database.models import model_base

URL_DATABASE = f'postgresql+psycopg2://{config.DB_USERNAME}:{config.DB_PASSWORD}@localhost:5432/{config.DB_DATABASE}'

database_engine = create_engine(URL_DATABASE)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=database_engine)

# Create all tables
model_base.metadata.create_all(bind=database_engine)