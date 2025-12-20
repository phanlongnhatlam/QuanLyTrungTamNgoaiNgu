# --- FILE: models.py ---
import enum
import hashlib
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, Boolean, text
from sqlalchemy.orm import relationship

# LƯU Ý: Đảm bảo tên package 'TrungTamNgoaiNgu' đúng với tên thư mục dự án của bạn
from TrungTamNgoaiNgu import db, app


# 1. ENUM
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


# 2. MODELS
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

    teacher_classes = relationship('Class', backref='teacher', lazy=True)
    student_enrollments = relationship('Enrollment', backref='student', lazy=True)
    invoices_processed = relationship('Invoice', backref='staff', lazy=True)

    def __str__(self): return self.name


class Course(db.Model):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    classes = relationship('Class', backref='course', lazy=True)

    def __str__(self): return self.name


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
    price = Column(Float, default=0.0)  # Thêm giá tiền nếu cần

    course_id = Column(Integer, ForeignKey(Course.id), nullable=False)
    teacher_id = Column(Integer, ForeignKey(User.id))
    enrollments = relationship('Enrollment', backref='my_class', lazy=True)

    def __str__(self): return self.name


class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_date = Column(DateTime, default=datetime.now())
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING)
    student_id = Column(Integer, ForeignKey(User.id), nullable=False)
    class_id = Column(Integer, ForeignKey(Class.id), nullable=False)
    grade = relationship('Grade', backref='enrollment', uselist=False, lazy=True)
    invoice = relationship('Invoice', backref='enrollment', uselist=False, lazy=True)
class Regulation(db.Model):
    __tablename__ = 'regulation'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True) # Tên quy định (VD: DIEM_CHUAN)
    value = Column(Float, default=0) # Giá trị (VD: 5.0)
    description = Column(String(200)) # Mô tả dễ hiểu (VD: Điểm trung bình để Đạt)

    def __str__(self):
        return self.description

class Grade(db.Model):
    __tablename__ = 'grade'
    id = Column(Integer, primary_key=True, autoincrement=True)
    average_score = Column(Float, default=0.0)
    result = Column(String(50))
    enrollment_id = Column(Integer, ForeignKey('enrollment.id'), nullable=False)
    details = relationship('GradeDetail', backref='grade', lazy=True)

    @property
    def calculate_average(self):
        if not self.details: return 0.0
        total_points = sum([d.score_value * d.weight for d in self.details])
        total_weights = sum([d.weight for d in self.details])
        if total_weights == 0: return 0.0
        return round(total_points / total_weights, 2)

    @property
    def hienthi(self):
        avg = self.calculate_average
        return "Đạt" if avg >= 5.0 else "Không đạt"


class GradeDetail(db.Model):
    __tablename__ = 'grade_detail'
    id = Column(Integer, primary_key=True, autoincrement=True)
    score_name = Column(String(50), nullable=False)
    score_value = Column(Float, default=0.0)
    weight = Column(Float, default=1.0)
    grade_id = Column(Integer, ForeignKey('grade.id'), nullable=False)


class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    checkin_date = Column(DateTime, default=datetime.now())
    is_present = Column(Boolean, default=True)
    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)


class Invoice(db.Model):
    __tablename__ = 'invoice'
    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    enrollment_id = Column(Integer, ForeignKey(Enrollment.id), nullable=False)
    staff_id = Column(Integer, ForeignKey(User.id))


# --- DATA SEEDING (Đoạn này copy y chang đoạn code bạn gửi lúc nãy để tạo dữ liệu) ---
if __name__ == '__main__':
    with app.app_context():
        print(">>> ĐANG RESET DATABASE...")
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        db.drop_all()
        db.session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.create_all()

        # 1. USER
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

        # 2. COURSE
        c_eng = Course(name='Tiếng Anh', description='Đào tạo TOEIC, IELTS, Giao tiếp chuẩn Quốc tế')
        c_jap = Course(name='Tiếng Nhật', description='Tiếng Nhật sơ cấp đến cao cấp (JLPT)')
        c_kor = Course(name='Tiếng Hàn', description='Luyện thi Topik & Xuất khẩu lao động')
        c_fra = Course(name='Tiếng Pháp', description='Tiếng Pháp du học & Giao tiếp')
        db.session.add_all([c_eng, c_jap, c_kor, c_fra])
        db.session.commit()

        # 3. CLASS
        classes = [
            Class(name='[Eng] ENG-COMM-K01', room='P.101', schedule='T2-T4-T6 (19h30)', course_id=c_eng.id,
                  teacher_id=u_teacher_ielts.id, price=2500000),
            Class(name='[TOEIC 2KN] Luyện Đề 550+', room='Lab 1', schedule='T3-T5-T7 (18h00)', course_id=c_eng.id,
                  teacher_id=u_teacher_toeic.id, price=1800000),
            Class(name='[IELTS] Foundation 5.0+', room='P.VIP', schedule='T2-T4-T6 (18h00)', course_id=c_eng.id,
                  teacher_id=u_teacher_ielts.id, price=5000000),
            Class(name='[N5] Tiếng Nhật Vỡ Lòng', room='P.201', schedule='T2-T4-T6 (17h30)', course_id=c_jap.id,
                  teacher_id=u_teacher_jap.id, price=1500000),
            Class(name='[Topik I] Hàn Ngữ Nhập Môn', room='P.301', schedule='T2-T4 (18h00)', course_id=c_kor.id,
                  teacher_id=u_teacher_kor.id, price=1600000),
            Class(name='[France] Pháp ngữ Nhập Môn', room='P.301', schedule='T2-T4 (18h00)', course_id=c_fra.id,
                  teacher_id=u_teacher_fra.id, price=1600000),
        ]
        db.session.add_all(classes)
        db.session.commit()

        r1 = Regulation(name='PASSING_SCORE', value=5.0, description='Điểm trung bình chuẩn để ĐẬU')
        r2 = Regulation(name='MAX_STUDENTS', value=40, description='Sĩ số tối đa của một lớp')
        r3 = Regulation(name='MIN_AGE', value=18, description='Độ tuổi tối thiểu đăng ký học')

        db.session.add_all([r1, r2, r3])
        db.session.commit()
        print(">>> ĐÃ TẠO DỮ LIỆU THÀNH CÔNG!")