import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker,declarative_base
from dotenv import load_dotenv
class Base(DeclarativeBase):
    pass
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL').strip()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base = declarative_base()
def get_session():
    with SessionLocal() as session:
        yield session
# just for testing the db connection
# if __name__ == "__main__":
#     conn = engine.connect()
#     print("Connected to db")
#     conn.close()        