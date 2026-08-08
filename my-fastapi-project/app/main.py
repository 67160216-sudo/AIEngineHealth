import os  # <-- เพิ่มบรรทัดนี้ไว้บนสุด
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List

app = FastAPI(
    title="AI Engine Health Prediction API",
    description="REST API สำหรับระบบทำนายสุขภาพเครื่องยนต์และจัดการผู้ใช้งาน",
    version="1.0.0"
)

# ==========================================
# Mock Database (ฐานข้อมูลจำลองในหน่วยความจำ)
# ==========================================
db_users = [
    {"id": 1, "username": "somchai", "email": "somchai@example.com", "full_name": "สมชาย สุขใจ", "password": "password123"},
    {"id": 2, "username": "saree", "email": "saree@example.com", "full_name": "สารี มั่นคง", "password": "password456"}
]
app = FastAPI(title="AI Engine Health Prediction API")

# <-- เพิ่ม 2 บรรทัดนี้ไว้หลังสร้างตัวแปร app (เพื่อให้เปิดหน้าเว็บ HTML ผ่าน Docker ได้)
if os.path.exists("app/static"):
    app.mount("/web", StaticFiles(directory="app/static", html=True), name="static")
# ==========================================
# Pydantic Schemas
# ==========================================
class RegisterSchema(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str

class LoginSchema(BaseModel):
    username: str
    password: str

class PasswordChangeSchema(BaseModel):
    old_password: str
    new_password: str

class UserUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str

class PredictionRequestSchema(BaseModel):
    coolant_temp: float
    battery_voltage: float
    rpm: int

# ==========================================
# 1. Authentication Endpoints
# ==========================================
@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["1. Authentication"])
def register(user: RegisterSchema):
    for u in db_users:
        if u["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username นี้ถูกใช้งานแล้ว")
    
    new_user = {
        "id": len(db_users) + 1,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "password": user.password
    }
    db_users.append(new_user)
    return {"message": "สมัครสมาชิกสำเร็จ", "user_id": new_user["id"]}

@app.post("/login", tags=["1. Authentication"])
def login(credentials: LoginSchema):
    for u in db_users:
        if u["username"] == credentials.username and u["password"] == credentials.password:
            return {"message": "เข้าสู่ระบบสำเร็จ", "token": f"fake-jwt-token-for-{u['username']}"}
    raise HTTPException(status_code=401, detail="Username หรือ Password ไม่ถูกต้อง")

@app.post("/logout", tags=["1. Authentication"])
def logout():
    return {"message": "ออกจากระบบสำเร็จ"}

@app.post("/change-password", tags=["1. Authentication"])
def change_password(data: PasswordChangeSchema):
    # สมมติให้เปลี่ยนรหัสผ่านของ user id 1
    if db_users[0]["password"] != data.old_password:
        raise HTTPException(status_code=400, detail="รหัสผ่านเดิมไม่ถูกต้อง")
    db_users[0]["password"] = data.new_password
    return {"message": "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว"}

# ==========================================
# 2. User Management Endpoints (CRUD)
# ==========================================
@app.get("/me", response_model=UserResponse, tags=["2. User Management"])
def get_me():
    # ดึงข้อมูลผู้ใช้งานปัจจุบัน (Mockup ID = 1)
    return db_users[0]

@app.get("/check-username/{name}", tags=["2. User Management"])
def check_username(name: str):
    is_taken = any(u["username"].lower() == name.lower() for u in db_users)
    return {"username": name, "is_available": not is_taken}

@app.get("/users", response_model=List[UserResponse], tags=["2. User Management"])
def get_all_users(page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    start = (page - 1) * limit
    end = start + limit
    return db_users[start:end]

@app.get("/users/{id}", response_model=UserResponse, tags=["2. User Management"])
def get_user_by_id(id: int):
    for u in db_users:
        if u["id"] == id:
            return u
    raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งานนี้")

@app.put("/users/{id}", tags=["2. User Management"])
def update_user(id: int, data: UserUpdateSchema):
    for u in db_users:
        if u["id"] == id:
            if data.full_name:
                u["full_name"] = data.full_name
            if data.email:
                u["email"] = data.email
            return {"message": f"อัปเดตข้อมูล User ID {id} สำเร็จ", "updated_data": u}
    raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งานนี้")

@app.delete("/users/{id}", tags=["2. User Management"])
def delete_user(id: int):
    global db_users
    initial_length = len(db_users)
    db_users = [u for u in db_users if u["id"] != id]
    if len(db_users) == initial_length:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้งานนี้")
    return {"message": f"ลบ User ID {id} เรียบร้อยแล้ว"}

# ==========================================
# 3. AI Prediction Endpoint (สำหรับ Project กลุ่ม)
# ==========================================
@app.post("/predict", tags=["3. AI Prediction"])
def predict_engine(data: PredictionRequestSchema):
    if data.coolant_temp > 100 or data.battery_voltage < 11.8:
        return {
            "status": "DANGER",
            "risk_score": "88%",
            "remaining_useful_life_days": 14,
            "critical_component": "ปั๊มน้ำเสื่อมสภาพ / ความร้อนสูงเกิน",
            "recommendation": "ควรเข้าศูนย์บริการทันทีภายใน 3 วัน"
        }
    return {
        "status": "NORMAL",
        "risk_score": "12%",
        "remaining_useful_life_days": 180,
        "critical_component": "ไม่มี (ปกติทุกชิ้นส่วน)",
        "recommendation": "ใช้งานได้ตามปกติ เข้าตรวจเช็กตามระยะ"
    }
