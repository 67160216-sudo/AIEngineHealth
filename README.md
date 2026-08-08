My FastAPI Project
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
2. Install Dependencies
pip install -r requirements.txt
3. Run FastAPI
uvicorn app.main:app --reload

เปิด Browser แล้วเข้า:

http://127.0.0.1:8000
🐳 Run with Docker
docker compose up --build

จากนั้นเข้า:

http://localhost:8000
📖 API Documentation

FastAPI มี API Documentation ให้อัตโนมัติ

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
HTML / CSS / JavaScript
Machine Learning
Docker
Docker Compose
📌 Project Status

🚧 This project is currently under development.