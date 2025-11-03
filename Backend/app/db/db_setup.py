# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:Hello7898.pgsql@localhost:5432/leaside"
#DATABASE_URL = "postgresql+psycopg2://postgres@localhost/Leaside"
engine = create_engine(DATABASE_URL, connect_args = {}, future = True) #the future helps use some async features
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future = True)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()