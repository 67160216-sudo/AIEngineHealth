from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# นำค่า Config จาก MySQL มหาวิทยาลัยมาใส่ตรงนี้
DB_USER = "s67160216"
DB_PASS = "cYTtf6pA"
DB_HOST = "127.0.0.1"
DB_NAME = "s67160216"

# รูปแบบ: mysql+pymysql://user:password@host:port/dbname
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:3306/{DB_NAME}?charset=utf8mb4"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()