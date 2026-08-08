# 🚗 AI Engine Health Prediction REST API & Simulation Web App

ระบบ REST API และเว็บแอปพลิเคชันจำลองการทำนายสุขภาพเครื่องยนต์รถยนต์ล่วงหน้าด้วย AI (Predictive Maintenance) สำหรับโปรเจกต์รายวิชา โดยใช้ **FastAPI** ร่วมกับ **Docker & Docker Compose** ตามมาตรฐานการพัฒนาซอฟต์แวร์

---

## 📌 คุณสมบัติของระบบ (Features)

1. **Authentication API:**
   - `POST /register` - สมัครสมาชิกใหม่
   - `POST /login` - เข้าสู่ระบบ
   - `POST /logout` - ออกจากระบบ
   - `POST /change-password` - เปลี่ยนรหัสผ่าน

2. **User Management API (CRUD):**
   - `GET /me` - ดึงข้อมูลผู้ใช้งานปัจจุบัน
   - `GET /users` - ดึงรายชื่อผู้ใช้งานทั้งหมด (รองรับ Pagination)
   - `GET /users/{id}` - ดึงข้อมูลผู้ใช้งานตาม ID
   - `PUT /users/{id}` - แก้ไขข้อมูลผู้ใช้งาน
   - `DELETE /users/{id}` - ลบข้อมูลผู้ใช้งาน
   - `GET /check-username/{name}` - ตรวจสอบว่า Username ซ้ำหรือไม่

3. **AI Engine Prediction API:**
   - `POST /predict` - ประมวลผลและทำนายโอกาสเครื่องยนต์ขัดข้อง อายุการใช้งานที่เหลือ (RUL) และชิ้นส่วนที่เสี่ยงเสียหาย

4. **Web UI & Sensor Simulator:**
   - หน้า Login, Register และ Prediction UI สำหรับสาธิตการใช้งาน
   - รองรับ **Sensor Simulator (Preset Buttons)** เพื่อจำลองสถานการณ์รถปกติ / เฝ้าระวัง / เครื่องยนต์เสี่ยงพัง สำหรับนำเสนอสไลด์งาน

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
my-fastapi-project/
├── app/
│   ├── main.py              # โค้ดหลักของ FastAPI และ REST API Endpoints
│   └── static/              # หน้าเว็บ UI (HTML/CSS/JS)
│       ├── login.html       # หน้าเข้าสู่ระบบ
│       ├── register.html    # หน้าสมัครสมาชิก
│       └── prediction.html  # หน้าทำนายผล AI & Sensor Simulator
├── Dockerfile               # ไฟล์กำหนดการสร้าง Container Image (Python 3.10)
├── docker-compose.yml       # ไฟล์จัดการ Container Service
├── requirements.txt         # รายชื่อ Python Packages ที่ต้องใช้
└── README.md                # เอกสารอธิบายการใช้งานโปรเจกต์









สั่งรันด้วย Docker CLI (ตามขั้นตอนในสไลด์)
Build Docker Image:

Bash
docker build -t course-api .
Run Docker Container:

Bash
docker run -d -p 8000:8000 --name course-api-container course-api
หยุดการทำงานและลบ Container:

Bash
docker rm -f course-api-container
