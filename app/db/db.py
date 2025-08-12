from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)