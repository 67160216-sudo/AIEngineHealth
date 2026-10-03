from sqlalchemy import Column, Integer, String, Float, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    predictions = relationship("Prediction", back_populates="owner")
    engine_checks = relationship("EngineCheck", back_populates="owner")


class EngineCheck(Base):
    """ตารางใหม่: ผลประเมินความเสี่ยงเครื่องยนต์ (โมเดล engine_model.pkl)"""
    __tablename__ = "engine_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vehicle_name = Column(String(100), nullable=False)

    # ค่าเซนเซอร์ 6 ตัว (ชื่อตรงกับ feature ของโมเดล)
    engine_rpm = Column(Float, nullable=False)
    lub_oil_pressure = Column(Float, nullable=False)
    fuel_pressure = Column(Float, nullable=False)
    coolant_pressure = Column(Float, nullable=False)
    lub_oil_temp = Column(Float, nullable=False)
    coolant_temp = Column(Float, nullable=False)

    # ผลลัพธ์
    risk_percent = Column(Float, nullable=False)       # ความเสี่ยงสุดท้าย (AI + กฎวิศวกรรม)
    ai_risk_percent = Column(Float, nullable=True)     # ความเสี่ยงจาก AI อย่างเดียว
    health_percent = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # normal / warning / danger

    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    owner = relationship("User", back_populates="engine_checks")


class Prediction(Base):
    """ตารางเก่า (โมเดล RUL เดิม) เก็บไว้เพื่อไม่ให้ข้อมูลเดิมหาย ระบบใหม่ไม่ได้ใช้แล้ว"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vehicle_name = Column(String(100), nullable=False)
    engine_temp = Column(Float, nullable=False)
    oil_pressure = Column(Float, nullable=False)
    engine_rpm = Column(Float, nullable=False)
    battery_volt = Column(Float, nullable=False)
    engine_load = Column(Float, nullable=False)
    rul_hours = Column(Integer, nullable=False)
    rul_days = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    owner = relationship("User", back_populates="predictions")
