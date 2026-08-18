from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# รูปแบบ: mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>
# กรณีใช้ Docker Compose ชื่อ host จะเป็นชื่อ service เช่น 'db'
DATABASE_URL = "mysql+pymysql://root:rootpassword@db:3306/engine_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency สำหรับสร้าง Session ในแต่ละ Request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()