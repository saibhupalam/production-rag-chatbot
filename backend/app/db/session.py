from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os
from urllib.parse import quote_plus

encoded_password=quote_plus(
    settings.POSTGRES_PASSWORD
)

DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:"
    f"{encoded_password}@"
    f"{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/"
    f"{settings.POSTGRES_DB}"
)

engine=create_engine(
    DATABASE_URL
)

SessionLocal= sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)