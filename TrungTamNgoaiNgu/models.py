import enum
import hashlib
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship

from TrungTamNgoaiNgu import db, app

class UserRole(enum.Enum):
    ADMIN = 1  # Quản trị viên
    TEACHER = 2  # Giáo viên
    STAFF = 3  # Thu ngân
    STUDENT = 4  # Học viên

class ClassStatus(enum.Enum):
    OPEN = 1  # Đang mở đăng ký
    CLOSED = 2  # Đã chốt sĩ số
    FINISHED = 3  # Đã kết thúc

class EnrollmentStatus(enum.Enum):
    PENDING = 1  # Đã đăng ký, chờ đóng tiền
    PAID = 2  # Đã đóng tiền (Chính thức)
    CANCELLED = 3  # Đã hủy

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
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    # Quan hệ: Một khóa học có nhiều lớp (Sáng/Chiều/Tối)
    classes = relationship('Class', backref='course', lazy=True)
    def __str__(self):
        return self.name


class Class(db.Model):
    __tablename__ = 'class'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # VD: TA-GT-K01
    room = Column(String(50))  # VD: Phòng 101
    schedule = Column(String(100))  # VD: T2-T4-T6 (19h-21h)
    max_students = Column(Integer, default=25)
    start_date = Column(DateTime, default=datetime.now())  # Ngày khai giảng
    image = Column(String(300),
                   default="https://res.cloudinary.com/dy1unykph/image/upload/v1741254148/aa0aawermmvttshzvjhc.png")
    status = Column(Enum(ClassStatus), default=ClassStatus.OPEN)
    price = Column(Float, default=2000000)  # Mặc định 2 triệu
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

class Regulation(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True) # Tên quy định (VD: SiSoToiDa)
    value = Column(Integer, default=0) # Giá trị (VD: 40)
    description = Column(String(255), nullable=True) # Mô tả cho dễ hiểu
    def __str__(self):
        return self.name

# =========================================================
# 3. TẠO DỮ LIỆU MẪU (SEEDING DATA)
# =========================================================
if __name__ == '__main__':
    with app.app_context():
        # 1. Làm sạch và tạo lại bảng
        db.drop_all()  # Bỏ comment dòng này nếu muốn xóa sạch dữ liệu cũ làm lại từ đầu
        db.create_all()

        # Chỉ tạo dữ liệu nếu chưa có Admin
        # if not User.query.filter(User.username == 'admin').first():
        # --- A. TẠO USER (Giáo viên & Staff) ---

        hashed_pw = hashlib.md5('123456'.encode('utf-8')).hexdigest()

        u_admin = User(name='Quản Trị Viên', username='admin', password=hashed_pw, role=UserRole.ADMIN)
        u_staff = User(name='Lễ Tân (Thu Ngân)', username='staff', password=hashed_pw, role=UserRole.STAFF)

        # Giáo viên chuyên biệt
        u_teacher_toeic = User(name='Ms. Jenny (TOEIC)', username='jenny', password=hashed_pw,
                               role=UserRole.TEACHER)
        u_teacher_ielts = User(name='Mr. Mark (IELTS)', username='mark', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_jap = User(name='Cô Akira (Nhật)', username='akira', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_kor = User(name='Thầy Park (Hàn)', username='park', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_fra = User(name='Thầy Pierre (Pháp)', username='pierre', password=hashed_pw,
                             role=UserRole.TEACHER)
        u_student = User(name='Học Viên Mẫu', username='student', password=hashed_pw, role=UserRole.STUDENT)

        db.session.add_all(
            [u_admin, u_staff, u_teacher_toeic, u_teacher_ielts, u_teacher_jap, u_teacher_kor, u_teacher_fra,
             u_student])
        db.session.commit()

        # --- B. TẠO COURSE (Các Tab Ngôn Ngữ) ---
        # Đây là 4 cái Tab trên Menu của bạn
        c_eng = Course(name='Tiếng Anh', description='Đào tạo TOEIC, IELTS, Giao tiếp chuẩn Quốc tế')
        c_jap = Course(name='Tiếng Nhật', description='Tiếng Nhật sơ cấp đến cao cấp (JLPT)')
        c_kor = Course(name='Tiếng Hàn', description='Luyện thi Topik & Xuất khẩu lao động')
        c_fra = Course(name='Tiếng Pháp', description='Tiếng Pháp du học & Giao tiếp')

        db.session.add_all([c_eng, c_jap, c_kor, c_fra])
        db.session.commit()

        # --- C. TẠO CLASS (Các lớp cụ thể theo yêu cầu của bạn) ---
        classes = [
            # ================= TIẾNG ANH (Đa dạng thể loại) =================
            # 1. Tiếng Anh Giao Tiếp
            Class(name='[Giao Tiếp] ENG-COMM-K01', room='P.101', schedule='T2-T4-T6 (19h30)',
                  course_id=c_eng.id, teacher_id=u_teacher_ielts.id,
                  image="https://th.bing.com/th/id/OIP.MRnmMkq6rO3XEoT8d_nqgAHaEj?w=292&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 2. TOEIC 2 Kỹ Năng (Nghe - Đọc)
            Class(name='[TOEIC 2KN] Luyện Đề 550+', room='Lab 1', schedule='T3-T5-T7 (18h00)',
                  course_id=c_eng.id, teacher_id=u_teacher_toeic.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 3. TOEIC 4 Kỹ Năng (Nghe - Nói - Đọc - Viết)
            Class(name='[TOEIC 4KN] Toàn Diện', room='Lab 2', schedule='T7-CN (08h00 - 11h00)',
                  course_id=c_eng.id, teacher_id=u_teacher_toeic.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 4. IELTS (Academic)
            Class(name='[IELTS] Foundation 5.0+', room='P.VIP', schedule='T2-T4-T6 (18h00)',
                  course_id=c_eng.id, teacher_id=u_teacher_ielts.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # ================= TIẾNG NHẬT (Theo cấp độ N) =================
            # 1. N5 (Sơ cấp)
            Class(name='[N5] Tiếng Nhật Vỡ Lòng', room='P.201', schedule='T2-T4-T6 (17h30)',
                  course_id=c_jap.id, teacher_id=u_teacher_jap.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 2. N4 (Sơ cấp 2)
            Class(name='[N4] Minna no Nihongo II', room='P.202', schedule='T3-T5-T7 (19h30)',
                  course_id=c_jap.id, teacher_id=u_teacher_jap.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 3. Luyện thi JLPT
            Class(name='[Luyện Thi] JLPT N3 Cấp Tốc', room='P.203', schedule='T7-CN (14h00)',
                  course_id=c_jap.id, teacher_id=u_teacher_jap.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # ================= TIẾNG HÀN (Theo Topik) =================
            # 1. Sơ cấp 1
            Class(name='[Topik I] Hàn Ngữ Nhập Môn', room='P.301', schedule='T2-T4 (18h00)',
                  course_id=c_kor.id, teacher_id=u_teacher_kor.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 2. Giao tiếp văn phòng
            Class(name='[Giao Tiếp] Tiếng Hàn Văn Phòng', room='P.302', schedule='CN (Full ngày)',
                  course_id=c_kor.id, teacher_id=u_teacher_kor.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # ================= TIẾNG PHÁP (Theo khung châu Âu) =================
            # 1. A1 Débutant
            Class(name='[A1] Tiếng Pháp Cơ Bản', room='P.401', schedule='T3-T5 (18h00)',
                  course_id=c_fra.id, teacher_id=u_teacher_fra.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # 2. Luyện thi DELF
            Class(name='[DELF B1] Luyện Thi B1', room='P.402', schedule='T7-CN (09h00)',
                  course_id=c_fra.id, teacher_id=u_teacher_fra.id,
                  image="https://th.bing.com/th/id/OIP.2TKCk3xdftw6tNrr8VO6YQHaEK?w=284&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),
        ]

        db.session.add_all(classes)
        db.session.commit()

        print(">>> ĐÃ TẠO DỮ LIỆU THÀNH CÔNG VỚI ĐẦY ĐỦ CÁC LOẠI LỚP!")
