import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.database.connection import engine
from app.database.models import Base

if __name__ == "__main__":
  Base.metadata.create_all(bind=engine)
  print("Database tables created successfully.")