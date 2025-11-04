import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


#------------ JWT -------------
SECRET_KEY = os.getenv("SECRET_KEY", "d8f2eaec849b83c454b43f859b9b491b")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


#------------ Database ------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///library.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
