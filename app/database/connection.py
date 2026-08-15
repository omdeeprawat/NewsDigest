import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
  user = os.getenv("POSTGRES_USER", "postgres")
  password = os.getenv("POSTGRES_PASSWORD", "postgres")
  host = os.getenv("DB_HOST", "localhost")
  port = os.getenv("DB_PORT", "5432")
  db = os.getenv("DB_NAME", "newsdigest")

  return f"postgresql://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(get_database_url())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
  return SessionLocal()
