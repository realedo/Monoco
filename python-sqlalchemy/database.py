from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Subscription, TokenLog, Domain, Prompt  # import your models

# ------------------ Engine ------------------
# SQLite database file will be created automatically if it doesn't exist
DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ------------------ Session ------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ------------------ Create tables ------------------
Base.metadata.create_all(bind=engine)

# ------------------ Helper functions ------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

