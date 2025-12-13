from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum, Date, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin
import enum
import hashlib

# LƯU Ý: Import từ package mới 'TrungTamNgoaiNgu'
from TrungTamNgoaiNgu import db, app


# --- 1. ĐỊNH NGHĨA CÁC ENUM ---
class UserRole(enum.Enum):
    ADMIN = 1
    TEACHER = 2
    STAFF = 3
    STUDENT = 4


class ClassStatus(enum.Enum):
    OPEN = 1  # Đang mở đăng ký
    CLOSED = 2  # Đã chốt sổ/Đang học
    FINISHED = 3  # Đã kết thúc


class EnrollmentStatus(enum.Enum):
    PENDING = 1
    PAID = 2
    CANCELLED = 3


# --- 2. CÁC MODEL (BẢNG) ---

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    avatar = Column(String(200),
                    default="https://res.cloudinary.com/dy1unykph/image/upload/v1631023267/avatar-default_y5323k.png")
    email = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.STUDENT)

    # Quan hệ
    teacher_classes = relationship('Class', backref='teacher', lazy=True)
    student_enrollments = relationship('Enrollment', backref='student', lazy=True)

    def __str__(self):
        return self.name


class Course(db.Model):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    fee = Column(Float, default=0.0)

    classes = relationship('Class', backref='course', lazy=True)

    def __str__(self):
        return self.name


class Class(db.Model):
    __tablename__ = 'class'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # VD: TA-K12
    course_id = Column(Integer, ForeignKey(Course.id), nullable=False)
    teacher_id = Column(Integer, ForeignKey(User.id))

    room = Column(String(50))
    schedule = Column(String(100))  # VD: T2-T4-T6
    max_students = Column(Integer, default=25)
    status = Column(Enum(ClassStatus), default=ClassStatus.OPEN)

    enrollments = relationship('Enrollment', backref='my_class', lazy=True)

    def __str__(self):
        return self.name


class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey(User.id), nullable=False)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING)

    # 1-1 với Điểm và Hóa đơn
    grade = relationship('Grade', backref='enrollment', uselist=False, lazy=True)
    invoice = relationship('Invoice', backref='enrollment', uselist=False, lazy=True)


class Grade(db.Model):
    __tablename__ = 'grade'
    id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)
    midterm_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)


class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True, autoincrement=True)
    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)
    staff_id = Column(Integer, ForeignKey(User.id))
    amount = Column(Float, nullable=False)
    created_date = Column(DateTime, default=datetime.now())


# --- 3. PHẦN TẠO DỮ LIỆU MẪU (CHẠY 1 LẦN LÀ CÓ DATA) ---
if __name__ == '__main__':
    # Đoạn này fix lỗi import tương đối khi chạy trực tiếp file models.py
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    with app.app_context():
        # A. Tạo bảng
        db.create_all()

        # B. Tạo Admin (Nếu chưa có)
        if not User.query.filter(User.username == 'admin').first():
            password = hashlib.md5('123456'.encode('utf-8')).hexdigest()
            admin = User(name='Quản trị viên', username='admin', password=password, role=UserRole.ADMIN)
            db.session.add(admin)

            # C. Tạo Giáo viên mẫu
            teacher = User(name='Thầy B', username='teacher1', password=password, role=UserRole.TEACHER)
            db.session.add(teacher)

            # D. Tạo Khóa học mẫu (Course)
            c1 = Course(name='Tiếng Anh Giao Tiếp', fee=1500000)
            c2 = Course(name='Luyện thi TOEIC 550+', fee=2000000)
            c3 = Course(name='Tiếng Anh Thiếu Nhi', fee=1200000)
            db.session.add_all([c1, c2, c3])

            # Lưu khóa học để lấy ID
            db.session.commit()

            # E. Tạo Lớp học mẫu (Class) - Gắn vào khóa học vừa tạo
            cl1 = Class(name='TA-GT-K01', course_id=c1.id, teacher_id=teacher.id, schedule='2-4-6 (19h-21h)',
                        room='P101')
            cl2 = Class(name='TOEIC-K02', course_id=c2.id, teacher_id=teacher.id, schedule='3-5-7 (18h-20h)',
                        room='Lab 3')

            db.session.add_all([cl1, cl2])

            db.session.commit()
            print(">>> ĐÃ KHỞI TẠO DỮ LIỆU THÀNH CÔNG! (Admin/123456)")
        else:
            print(">>> Dữ liệu đã tồn tại, không cần tạo thêm.")
if __name__ == '__main__':
    app.run()
