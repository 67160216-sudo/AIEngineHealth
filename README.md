My FastAPI Project

โปรเจกต์ Web Application สำหรับระบบ AI Engine Health Prediction พัฒนาด้วย FastAPI โดยมีระบบจัดการผู้ใช้งานและหน้าสำหรับทำนายสุขภาพเครื่องยนต์

📁 Project Structure
my-fastapi-project/
│
├── app/
│   ├── main.py
│   │
│   └── static/
│       ├── login.html
│       ├── register.html
│       └── prediction.html
│
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
📂 รายละเอียดแต่ละไฟล์
ไฟล์ / โฟลเดอร์	รายละเอียด
app/	โฟลเดอร์หลักของ Application
app/main.py	FastAPI REST API และ Backend หลักของระบบ
app/static/	เก็บไฟล์ Frontend ของระบบ
login.html	หน้าสำหรับเข้าสู่ระบบ
register.html	หน้าสำหรับสมัครสมาชิก
prediction.html	หน้าสำหรับทำนายสุขภาพเครื่องยนต์
requirements.txt	รายการ Python Packages ที่โปรเจกต์ต้องใช้
Dockerfile	ไฟล์สำหรับสร้าง Docker Image
docker-compose.yml	ใช้สำหรับจัดการและรัน Container ของโปรเจกต์
🚀 Installation
1. Clone Repository
git clone <repository-url>
cd my-fastapi-project
2. ติดตั้ง Dependencies
pip install -r requirements.txt
3. Run FastAPI
uvicorn app.main:app --reload

จากนั้นเปิดเว็บไซต์:

http://127.0.0.1:8000
🐳 Run with Docker

สามารถรันโปรเจกต์ด้วย Docker Compose ได้ด้วยคำสั่ง:

docker compose up --build

เมื่อ Container ทำงานแล้ว สามารถเข้าใช้งานผ่าน:

http://localhost:8000
📖 API Documentation

FastAPI จะสร้าง API Documentation ให้อัตโนมัติ

Swagger UI
http://localhost:8000/docs
ReDoc
http://localhost:8000/redoc
✨ Features
🔐 User Login
📝 User Registration
🚗 Engine Health Prediction
🤖 AI / Machine Learning Prediction
🌐 REST API ด้วย FastAPI
🐳 Docker Support
📊 Prediction Web Interface
🛠️ Technologies
Python
FastAPI
REST API
HTML / CSS / JavaScript
Machine Learning
Docker
Docker Compose
📌 Project Status

🚧 This project is currently under development.

Developed for educational / university project purposes.
