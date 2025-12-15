from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin
import enum
import hashlib
# LƯU Ý: Sửa dòng này thành tên package của bạn (ví dụ: from saleapp import db, app)
# Nếu file __init__.py nằm cùng cấp thì dùng: from __init__ import db, app
from TrungTamNgoaiNgu import db, app


# =========================================================
# 1. ĐỊNH NGHĨA CÁC ENUM (TRẠNG THÁI & VAI TRÒ)
# =========================================================

class UserRole(enum.Enum):
    ADMIN = 1  # Quản trị viên
    TEACHER = 2  # Giáo viên
    STAFF = 3  # Nhân viên (Thu ngân/Giáo vụ)
    STUDENT = 4  # Học viên


class ClassStatus(enum.Enum):
    OPEN = 1  # Đang mở đăng ký
    CLOSED = 2  # Đã chốt sổ / Đang học
    FINISHED = 3  # Đã kết thúc


class EnrollmentStatus(enum.Enum):
    PENDING = 1  # Đã đăng ký, chờ đóng tiền
    PAID = 2  # Đã đóng tiền (Chính thức)
    CANCELLED = 3  # Đã hủy


# =========================================================
# 2. ĐỊNH NGHĨA CÁC BẢNG (MODELS)
# =========================================================

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
    invoices_processed = relationship('Invoice', backref='staff', lazy=True)  # Hóa đơn do nhân viên nào lập

    def __str__(self):
        return self.name


class Course(db.Model):
    """
    Bảng này đóng vai trò như 'Danh mục' trên Menu.
    VD: Tiếng Anh Giao Tiếp, Luyện thi TOEIC, Tiếng Nhật N5...
    """
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Quan hệ: Một khóa học có nhiều lớp (Sáng/Chiều/Tối)
    classes = relationship('Class', backref='course', lazy=True)

    def __str__(self):
        return self.name


class Class(db.Model):
    """
    Đây là sản phẩm cụ thể để học viên đăng ký.
    """
    __tablename__ = 'class'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # VD: TA-GT-K01
    room = Column(String(50))  # VD: Phòng 101
    schedule = Column(String(100))  # VD: T2-T4-T6 (19h-21h)
    max_students = Column(Integer, default=25)
    start_date = Column(DateTime, default=datetime.now())  # Ngày khai giảng

    status = Column(Enum(ClassStatus), default=ClassStatus.OPEN)

    # Khóa ngoại
    course_id = Column(Integer, ForeignKey(Course.id), nullable=False)
    teacher_id = Column(Integer, ForeignKey(User.id))

    # Quan hệ
    enrollments = relationship('Enrollment', backref='my_class', lazy=True)

    def __str__(self):
        return self.name


class Enrollment(db.Model):
    """
    Phiếu ghi danh (Học viên đăng ký vào 1 lớp)
    """
    __tablename__ = 'enrollment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING)

    student_id = Column(Integer, ForeignKey(User.id), nullable=False)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=False)

    # 1-1 với Điểm và Hóa đơn
    grade = relationship('Grade', backref='enrollment', uselist=False, lazy=True)
    invoice = relationship('Invoice', backref='enrollment', uselist=False, lazy=True)


class Grade(db.Model):
    __tablename__ = 'grade'
    id = Column(Integer, primary_key=True, autoincrement=True)
    midterm_score = Column(Float, default=0.0)
    final_score = Column(Float, default=0.0)
    average_score = Column(Float, default=0.0)

    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)


class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    created_date = Column(DateTime, default=datetime.now())

    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)
    staff_id = Column(Integer, ForeignKey(User.id))  # Nhân viên thu ngân nào thu tiền


# =========================================================
# 3. TẠO DỮ LIỆU MẪU (SEEDING DATA)
# =========================================================
if __name__ == '__main__':
    with app.app_context():
        # A. Tạo bảng
        db.create_all()

        # B. Kiểm tra xem có dữ liệu chưa, nếu chưa thì tạo mới
        if not User.query.filter(User.username == 'admin').first():

            # --- 1. TẠO USER (4 Role) ---
            hashed_pw = hashlib.md5('123456'.encode('utf-8')).hexdigest()

            u_admin = User(name='Quản Trị Viên', username='admin', password=hashed_pw, role=UserRole.ADMIN)
            u_staff = User(name='Thu Ngân Viên', username='staff', password=hashed_pw, role=UserRole.STAFF)
            u_teacher1 = User(name='Thầy Tuấn (IELTS)', username='teacher1', password=hashed_pw, role=UserRole.TEACHER)
            u_teacher2 = User(name='Cô Lan (Nhật)', username='teacher2', password=hashed_pw, role=UserRole.TEACHER)
            u_student = User(name='Nguyễn Văn Học', username='student', password=hashed_pw, role=UserRole.STUDENT)

            db.session.add_all([u_admin, u_staff, u_teacher1, u_teacher2, u_student])
            db.session.commit()

            # --- 2. TẠO COURSE (Các tab trên Menu) ---
            c1 = Course(name='Tiếng Anh', description='0 bt nx')
            c2 = Course(name='Tiếng Nhật', description='Cam kết đầu ra 6.0+')
            c3 = Course(name='Tiếng Pháp', description='Nhập môn tiếng Nhật')
            c4 = Course(name='Tiếng Hàn', description='Sơ cấp tiếng Hàn')

            db.session.add_all([c1, c2, c3, c4])
            db.session.commit()

            # --- 3. TẠO CLASS (Các lớp cụ thể để đăng ký) ---
            classes = [
                # Lớp Tiếng Anh Giao Tiếp (c1)
                Class(name='TA-GT-Sáng', room='P101', schedule='T2-T4-T6 (08h-10h)', course_id=c1.id,
                      teacher_id=u_teacher1.id),
                Class(name='TA-GT-Tối', room='P102', schedule='T3-T5-T7 (19h-21h)', course_id=c1.id,
                      teacher_id=u_teacher1.id),

                # Lớp IELTS (c2)
                Class(name='IELTS-Cấp Tốc', room='Lab 1', schedule='T7-CN (Full ngày)', course_id=c2.id,
                      teacher_id=u_teacher1.id),

                # Lớp Tiếng Nhật (c3)
                Class(name='JP-N5-K12', room='P205', schedule='T2-T4-T6 (18h-20h)', course_id=c3.id,
                      teacher_id=u_teacher2.id),

                # Lớp Tiếng Hàn (c4)
                Class(name='KR-Topik-K01', room='P301', schedule='T3-T5 (18h-20h)', course_id=c4.id,
                      teacher_id=u_teacher2.id)
            ]

            db.session.add_all(classes)
            db.session.commit()
