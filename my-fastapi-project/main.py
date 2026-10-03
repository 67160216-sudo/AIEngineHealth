from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from engine_ai import EngineAI, engineering_checks

# สร้างตารางที่ยังไม่มีอัตโนมัติ (จะสร้าง engine_checks ให้ ตารางเดิมไม่ถูกแตะ)
models.Base.metadata.create_all(bind=engine)


def ensure_columns():
    """เพิ่มคอลัมน์ใหม่ให้ตารางที่มีอยู่แล้ว (create_all ไม่เพิ่มคอลัมน์ให้ตารางเดิม)"""
    cols = {c["name"] for c in inspect(engine).get_columns("engine_checks")}
    if "ai_risk_percent" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE engine_checks ADD COLUMN ai_risk_percent FLOAT NULL AFTER risk_percent"))
        print("✅ เพิ่มคอลัมน์ ai_risk_percent ในตาราง engine_checks แล้ว")


ensure_columns()

app = FastAPI(title="AI Engine Health API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# โหลดโมเดล AI ครั้งเดียวตอนเริ่มเซิร์ฟเวอร์
engine_ai = EngineAI()


# ==========================================
# Schemas
# ==========================================
class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str


class LoginSchema(BaseModel):
    username: str
    password: str


class SensorValues(BaseModel):
    # ขอบเขตกว้าง ๆ แค่กันค่าที่เป็นไปไม่ได้ (ค่าแปลกแต่เป็นไปได้จะได้คำเตือนแทน)
    engine_rpm: float = Field(ge=0, le=10000)
    lub_oil_pressure: float = Field(ge=0, le=20)
    fuel_pressure: float = Field(ge=0, le=50)
    coolant_pressure: float = Field(ge=0, le=20)
    lub_oil_temp: float = Field(ge=-40, le=200)
    coolant_temp: float = Field(ge=-40, le=250)
    # รอบสูงสุดระหว่างขับ (ไม่บังคับ) ใช้กับเกณฑ์ Red line เท่านั้น AI ใช้ค่าขณะเดินเบา
    peak_rpm: Optional[float] = Field(default=None, ge=0, le=12000)


class EngineInput(SensorValues):
    user_id: int = Field(gt=0)
    vehicle_name: str = Field(default="", max_length=100)


class SimulateRequest(BaseModel):
    points: List[SensorValues]


# ==========================================
# Helpers
# ==========================================
def fmt_time(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""


def check_to_dict(r: models.EngineCheck) -> dict:
    values = {
        "engine_rpm": r.engine_rpm, "lub_oil_pressure": r.lub_oil_pressure,
        "fuel_pressure": r.fuel_pressure, "coolant_pressure": r.coolant_pressure,
        "lub_oil_temp": r.lub_oil_temp, "coolant_temp": r.coolant_temp,
    }
    return {
        "id": r.id,
        "vehicle_name": r.vehicle_name,
        "engine_rpm": r.engine_rpm,
        "lub_oil_pressure": r.lub_oil_pressure,
        "fuel_pressure": r.fuel_pressure,
        "coolant_pressure": r.coolant_pressure,
        "lub_oil_temp": r.lub_oil_temp,
        "coolant_temp": r.coolant_temp,
        "risk_percent": r.risk_percent,
        "ai_risk_percent": r.ai_risk_percent if r.ai_risk_percent is not None else r.risk_percent,
        "health_percent": r.health_percent,
        "status": r.status,
        "findings": engineering_checks(values),
        "created_at": fmt_time(r.created_at),
    }


# ==========================================
# Endpoints: ระบบ
# ==========================================
@app.get("/health", tags=["System"])
def health():
    return {"api": "ok", "model_ready": engine_ai.ready}


# ==========================================
# Endpoints: Authentication (เหมือนเดิม)
# ==========================================
@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register(user_data: RegisterSchema, db: Session = Depends(get_db)):
    clean_username = user_data.username.strip()
    clean_email = user_data.email.strip()

    if db.query(models.User).filter(models.User.username == clean_username).first():
        raise HTTPException(status_code=400, detail="Username นี้ถูกใช้งานแล้ว")
    if db.query(models.User).filter(models.User.email == clean_email).first():
        raise HTTPException(status_code=400, detail="Email นี้ถูกใช้งานแล้ว")

    new_user = models.User(
        username=clean_username,
        email=clean_email,
        full_name=user_data.full_name.strip(),
        password_hash=pwd_context.hash(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "ลงทะเบียนสำเร็จ",
        "user_id": new_user.id,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "email": new_user.email,
    }


@app.post("/login", tags=["Authentication"])
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    clean_username = credentials.username.strip()
    user = db.query(models.User).filter(
        (models.User.username == clean_username) | (models.User.email == clean_username)
    ).first()

    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Username หรือ Password ไม่ถูกต้อง")

    return {
        "message": "เข้าสู่ระบบสำเร็จ",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
        },
    }


# ==========================================
# Endpoints: AI ประเมินความเสี่ยงเครื่องยนต์
# ==========================================
@app.get("/engine/model-info", tags=["Engine AI"])
def model_info():
    """ข้อมูลสำหรับสร้างฟอร์มหน้าเว็บ: ชื่อ/หน่วย/ช่วงค่าแต่ละช่อง, เกณฑ์สถานะ, ผลวัดโมเดล"""
    return engine_ai.info()


@app.post("/engine/predict", tags=["Engine AI"])
def engine_predict(data: EngineInput, db: Session = Depends(get_db)):
    if not engine_ai.ready:
        raise HTTPException(status_code=503, detail="โมเดล AI ยังไม่พร้อมใช้งาน กรุณาแจ้งผู้ดูแลระบบ")

    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งาน กรุณาเข้าสู่ระบบใหม่")

    values = {f: getattr(data, f) for f in engine_ai.features}
    try:
        result = engine_ai.predict(values, data.peak_rpm)
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดระหว่างประมวลผลด้วย AI")

    vehicle_name = data.vehicle_name.strip() or f"ตรวจเช็ก {datetime.now():%Y-%m-%d %H:%M}"

    record = models.EngineCheck(
        user_id=data.user_id,
        vehicle_name=vehicle_name,
        **values,
        risk_percent=result["risk_percent"],
        ai_risk_percent=result["ai_risk_percent"],
        health_percent=result["health_percent"],
        status=result["status"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "ประเมินและบันทึกสำเร็จ",
        "data": check_to_dict(record),
        "warnings": result["warnings"],
        "adjusted_by_rules": result["adjusted_by_rules"],
        "thresholds": engine_ai.thresholds,
    }


@app.post("/engine/simulate", tags=["Engine AI"])
def engine_simulate(req: SimulateRequest):
    """ประเมินค่าจำลอง (ไม่บันทึกลงฐานข้อมูล) รับได้ครั้งละ 1-200 จุด"""
    if not engine_ai.ready:
        raise HTTPException(status_code=503, detail="โมเดล AI ยังไม่พร้อมใช้งาน")
    if not 1 <= len(req.points) <= 200:
        raise HTTPException(status_code=400, detail="ส่งข้อมูลได้ครั้งละ 1-200 จุด")

    results = []
    for p in req.points:
        values = {f: getattr(p, f) for f in engine_ai.features}
        results.append(engine_ai.predict(values, p.peak_rpm))
    return {"results": results, "thresholds": engine_ai.thresholds}


@app.get("/engine/history/{user_id}", tags=["Engine AI"])
def engine_history(user_id: int, db: Session = Depends(get_db)):
    records = (
        db.query(models.EngineCheck)
        .filter(models.EngineCheck.user_id == user_id)
        .order_by(models.EngineCheck.id.desc())
        .all()
    )
    return [check_to_dict(r) for r in records]


@app.delete("/engine/history/{record_id}", tags=["Engine AI"])
def engine_delete(record_id: int, user_id: int = Query(gt=0), db: Session = Depends(get_db)):
    # ลบได้เฉพาะรายการของตัวเอง
    record = (
        db.query(models.EngineCheck)
        .filter(models.EngineCheck.id == record_id, models.EngineCheck.user_id == user_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="ไม่พบรายการนี้")
    db.delete(record)
    db.commit()
    return {"message": "ลบรายการเรียบร้อยแล้ว"}
