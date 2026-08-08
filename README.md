🚀 ขั้นตอนการติดตั้งและเริ่มใช้งาน (Getting Started)
ข้อกำหนดก่อนเริ่มใช้งาน (Prerequisites)
มีการติดตั้ง Docker Desktop ในเครื่องเรียบร้อยแล้ว

Docker Desktop ตั้งค่าใช้งานโหมด Linux Containers

🟢 วิธีที่ 1: สั่งรันด้วย Docker Compose (แนะนำ)
เปิด Terminal / PowerShell แล้วเข้าไปที่โฟลเดอร์โปรเจกต์:

Bash
cd my-fastapi-project
สั่ง Build Image และ Run Container:

Bash
docker-compose up -d --build
ปิดการทำงานเมื่อพรีเซนต์เสร็จ:

Bash
docker-compose down
🔵 วิธีที่ 2: สั่งรันด้วย Docker CLI (ตามขั้นตอนในสไลด์)
Build Docker Image:

Bash
docker build -t course-api .
Run Docker Container:

Bash
docker run -d -p 8000:8000 --name course-api-container course-api
หยุดการทำงานและลบ Container:

Bash
docker rm -f course-api-container
🌐 ลิงก์สำหรับการเข้าใช้งาน (Access URLs)
เมื่อรัน Container สำเร็จแล้ว สามารถเข้าใช้งานผ่านเว็บเบราว์เซอร์ได้ที่:

Interactive API Documentation (Swagger UI):

👉 http://localhost:8000/docs

หน้าเข้าสู่ระบบ (Login Web UI):

👉 http://localhost:8000/web/login.html

หน้าทำนายผล AI (Prediction Dashboard & Simulator):

👉 http://localhost:8000/web/prediction.html

🛠️ เทคโนโลยีที่ใช้ (Tech Stack)
Backend: FastAPI, Uvicorn, Pydantic

Frontend: HTML5, CSS3, JavaScript (Vanilla JS), FontAwesome

Containerization: Docker, Docker Compose
