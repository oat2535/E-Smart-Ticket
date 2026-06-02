# Dockerfile

#Image สำหรับ Python 3.12 เรียกใช้งานจาก Docker Hub
FROM python:3.12-slim

# ติดตั้ง dependencies
# อัปเดตรายการแพ็กเกจ และติดตั้ง libpq-dev, build-essential, wget, postgresql-client
RUN apt-get update && apt-get install -y \ 
    # ไลบรารีสำหรับเชื่อมต่อ PostgreSQL
    libpq-dev \
    # เครื่องมือสำหรับการคอมไพล์โค้ด สำหรับการติดตั้ง Python packages ที่ต้องคอมไพล์ psycopg2 (Package สำหรับเชื่อมต่อ PostgreSQL ใน Python)
    build-essential \
    # เครื่องมือดาวน์โหลดไฟล์จากอินเทอร์เน็ตผ่าน HTTP, HTTPS, และ FTP
    wget \
    # ไคลเอนต์ PostgreSQL สำหรับการติดต่อกับเซิร์ฟเวอร์ PostgreSQL
    postgresql-client \ 
    # ลบแพ็กเกจที่ไม่ใช้แล้ว ลบแคชของ apt-get ที่อยู่ใน /var/lib/apt/lists/
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python packages
# อัปเดต pip และ setuptools
RUN pip install --no-cache-dir --upgrade pip setuptools

# ตั้งค่า timezone
ENV TZ=Asia/Bangkok
RUN echo "Asia/Bangkok" > /etc/timezone && \
    ln -sf /usr/share/zoneinfo/Asia/Bangkok /etc/localtime

# สร้างโฟลเดอร์สำหรับโปรเจค
WORKDIR /app

# คัดลอกไฟล์ requirements.txt
COPY requirements.txt /app/

# ติดตั้ง Package Python ทั้งหมดตามลิสรายการในไฟล์ requirements.txt
RUN pip install --no-cache-dir -r requirements.txt 

# คัดลอกไฟล์ใน Project 
COPY . /app/

# # คัดลอกไฟล์ตั้งค่า Nginx
# COPY ./nginx/conf/nginx.conf /etc/nginx/nginx.conf:ro
# COPY ./nginx/conf.d /etc/nginx/conf.d:ro

# Expose port
EXPOSE 8000

# คำสั่งสำหรับรัน Project โดยใช้คำสั่ง python manage.py runserver รับทุก IP Address ที่เชื่อมต่อเข้ามาที่พอร์ต 8000 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
