import enum
import hashlib
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, Boolean
from sqlalchemy.orm import relationship

from TrungTamNgoaiNgu import db, app


# ================= ENUMS =================
class UserRole(enum.Enum):
    ADMIN = 1
    TEACHER = 2
    STAFF = 3
    STUDENT = 4


class ClassStatus(enum.Enum):
    OPEN = 1
    CLOSED = 2
    FINISHED = 3


class EnrollmentStatus(enum.Enum):
    PENDING = 1
    PAID = 2
    CANCELLED = 3


# ================= MODELS =================

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}

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

    # [ĐÃ SỬA] Chỉ định rõ foreign_keys để tránh lỗi mơ hồ với Invoice
    # invoices_processed = relationship('Invoice', backref='staff', lazy=True) <--- DÒNG CŨ GÂY LỖI
    # Xử lý quan hệ này trực tiếp bên class Invoice cho gọn

    def __str__(self):
        return self.name


class Course(db.Model):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    classes = relationship('Class', backref='course', lazy=True)

    def __str__(self):
        return self.name


class Class(db.Model):
    __tablename__ = 'class'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    room = Column(String(50))
    schedule = Column(String(100))
    max_students = Column(Integer, default=25)
    start_date = Column(DateTime, default=datetime.now())
    image = Column(String(300),
                   default="https://res.cloudinary.com/dy1unykph/image/upload/v1741254148/aa0aawermmvttshzvjhc.png")
    status = Column(Enum(ClassStatus), default=ClassStatus.OPEN)
    price = Column(Float, default=2000000)

    course_id = Column(Integer, ForeignKey(Course.id), nullable=False)
    teacher_id = Column(Integer, ForeignKey(User.id))

    enrollments = relationship('Enrollment', backref='my_class', lazy=True)

    def __str__(self):
        return self.name


class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING)

    student_id = Column(Integer, ForeignKey(User.id), nullable=False)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=False)

    grade = relationship('Grade', backref='enrollment', uselist=False, lazy=True)

    # Quan hệ Invoice để nullable=True để tránh lỗi vòng lặp
    invoices = relationship('Invoice', backref='enrollment', lazy=True)


class Grade(db.Model):
    __tablename__ = 'grade'
    id = Column(Integer, primary_key=True, autoincrement=True)
    midterm_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)

    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)


class Invoice(db.Model):
    __tablename__ = 'invoice'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    status = Column(Boolean, default=False)

    # [QUAN TRỌNG] SỬA LẠI QUAN HỆ ĐỂ TRÁNH LỖI AMBIGUOUS
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    # foreign_keys=[user_id]: Chỉ định rõ ràng đây là liên kết tới Học viên
    user = relationship('User', foreign_keys=[user_id], backref='invoices')

    staff_id = Column(Integer, ForeignKey(User.id), nullable=True)
    # foreign_keys=[staff_id]: Chỉ định rõ ràng đây là liên kết tới Thu ngân
    staff = relationship('User', foreign_keys=[staff_id], backref='processed_invoices')

    # Cho phép null để tạo hóa đơn trước khi có enrollment (Cho chức năng Giỏ hàng)
    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=True)


class Regulation(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    value = Column(Integer, default=0)
    description = Column(String(255), nullable=True)

    def __str__(self):
        return self.name


# ================= DATA SEEDING =================
if __name__ == '__main__':
    with app.app_context():
        # Xóa và tạo lại bảng
        db.drop_all()
        db.create_all()

        # 1. TẠO USER
        hashed_pw = hashlib.md5('123456'.encode('utf-8')).hexdigest()

        u_admin = User(name='Quản Trị Viên', username='admin', password=hashed_pw, role=UserRole.ADMIN)
        u_staff = User(name='Lễ Tân (Thu Ngân)', username='staff', password=hashed_pw, role=UserRole.STAFF)
        u_student = User(name='Học Viên Mẫu', username='student', password=hashed_pw, role=UserRole.STUDENT)

        u_teacher_toeic = User(name='Ms. Jenny (TOEIC)', username='jenny', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_ielts = User(name='Mr. Mark (IELTS)', username='mark', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_jap = User(name='Cô Akira (Nhật)', username='akira', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_kor = User(name='Thầy Park (Hàn)', username='park', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_fra = User(name='Thầy Pierre (Pháp)', username='pierre', password=hashed_pw, role=UserRole.TEACHER)

        db.session.add_all([u_admin, u_staff, u_student, u_teacher_toeic, u_teacher_ielts, u_teacher_jap, u_teacher_kor,
                            u_teacher_fra])
        db.session.commit()

        # 2. TẠO COURSE
        c_eng = Course(name='Tiếng Anh', description='Đào tạo TOEIC, IELTS, Giao tiếp chuẩn Quốc tế')
        c_jap = Course(name='Tiếng Nhật', description='Tiếng Nhật sơ cấp đến cao cấp (JLPT)')
        c_kor = Course(name='Tiếng Hàn', description='Luyện thi Topik & Xuất khẩu lao động')
        c_fra = Course(name='Tiếng Pháp', description='Tiếng Pháp du học & Giao tiếp')

        db.session.add_all([c_eng, c_jap, c_kor, c_fra])
        db.session.commit()

        # 3. TẠO CLASS (Đã cập nhật giá tiền đầy đủ)
        classes = [
            Class(name='[Giao Tiếp] ENG-COMM-K01', room='Phòng A1', schedule='T2-T4-T6 (19h30)',
                  course_id=c_eng.id, teacher_id=u_teacher_ielts.id, price=2500000,
                  image="https://th.bing.com/th/id/OIP.MRnmMkq6rO3XEoT8d_nqgAHaEj?w=292&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[TOEIC 2KN] Luyện Đề 550+', room='Lab 1', schedule='T3-T5-T7 (18h00)',
                  course_id=c_eng.id, teacher_id=u_teacher_toeic.id, price=1800000,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[IELTS] Foundation 5.0+', room='P.VIP', schedule='T2-T4-T6 (18h00)',
                  course_id=c_eng.id, teacher_id=u_teacher_ielts.id, price=5000000,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[N5] Tiếng Nhật Vỡ Lòng', room='P.201', schedule='T2-T4-T6 (17h30)',
                  course_id=c_jap.id, teacher_id=u_teacher_jap.id, price=1500000,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Luyện Thi] JLPT N3 Cấp Tốc', room='P.203', schedule='T7-CN (14h00)',
                  course_id=c_jap.id, teacher_id=u_teacher_jap.id, price=3200000,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Topik I] Hàn Ngữ Nhập Môn', room='P.301', schedule='T2-T4 (18h00)',
                  course_id=c_kor.id, teacher_id=u_teacher_kor.id, price=1600000,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),
        ]

        db.session.add_all(classes)
        db.session.commit()

        print(">>> ĐÃ TẠO DỮ LIỆU THÀNH CÔNG VỚI ĐẦY ĐỦ CÁC LOẠI LỚP!")