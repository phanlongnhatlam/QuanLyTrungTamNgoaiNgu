import enum
import hashlib
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text, Boolean, text
from sqlalchemy.orm import relationship
from TrungTamNgoaiNgu import db, app

class UserRole(enum.Enum):
    ADMIN = 1
    TEACHER = 2
    CASHIER = 3
    STUDENT = 4


class ClassStatus(enum.Enum):
    OPEN = 1
    CLOSED = 2
    FINISHED = 3

class EnrollmentStatus(enum.Enum):
    PENDING = 1
    PAID = 2
    CANCELLED = 3

class User(db.Model, UserMixin):
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
    invoices_processed = relationship('Invoice', backref='cashier', lazy=True)
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
    cashier_id = Column(Integer, ForeignKey(User.id))

if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        # =================================================================
        # 1. TẠO USER (GIÁO VIÊN & NHÂN VIÊN)
        # =================================================================
        hashed_pw = hashlib.md5('123456'.encode('utf-8')).hexdigest()

        # Admin & Staff
        u_admin = User(name='Quản Trị Viên', username='admin', password=hashed_pw, role=UserRole.ADMIN)
        u_cashier = User(name='Thu Ngân Viên', username='cashier', password=hashed_pw, role=UserRole.CASHIER)
        u_student = User(name='Học Viên Test', username='student', password=hashed_pw, role=UserRole.STUDENT)

        # Giáo viên theo bộ môn
        u_teacher_toeic = User(name='Ms. Jenny (TOEIC)', username='jenny', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_ielts = User(name='Mr. Mark (IELTS)', username='mark', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_jap = User(name='Cô Akira (Nhật)', username='akira', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_kor = User(name='Thầy Park (Hàn)', username='park', password=hashed_pw, role=UserRole.TEACHER)
        u_teacher_fra = User(name='Thầy Pierre (Pháp)', username='pierre', password=hashed_pw, role=UserRole.TEACHER)

        db.session.add_all([u_admin, u_cashier, u_student, u_teacher_toeic, u_teacher_ielts, u_teacher_jap, u_teacher_kor,
                            u_teacher_fra])
        db.session.commit()

        # =================================================================
        # 2. TẠO COURSE (KHÓA HỌC)
        # =================================================================
        c_eng = Course(name='Tiếng Anh', description='Đào tạo TOEIC, IELTS, Giao tiếp chuẩn Quốc tế')
        c_jap = Course(name='Tiếng Nhật', description='Tiếng Nhật sơ cấp đến cao cấp (JLPT)')
        c_kor = Course(name='Tiếng Hàn', description='Luyện thi Topik & Xuất khẩu lao động')
        c_fra = Course(name='Tiếng Pháp', description='Tiếng Pháp du học & Giao tiếp')

        db.session.add_all([c_eng, c_jap, c_kor, c_fra])
        db.session.commit()

        # =================================================================
        # 3. TẠO CLASS (20 LỚP THỦ CÔNG)
        # =================================================================
        classes = [
            # --- NHÓM 1: TIẾNG ANH (TOEIC & IELTS) ---
            Class(name='[TOEIC] Giải đề cấp tốc 550+', room='P.101', schedule='T2-T4-T6 (17h30)', price=1800000,
                  teacher_id=u_teacher_toeic.id, course_id=c_eng.id),
            Class(name='[TOEIC] Basic cho người mất gốc', room='P.102', schedule='T3-T5-T7 (19h30)', price=1500000,
                  teacher_id=u_teacher_toeic.id, course_id=c_eng.id),
            Class(name='[IELTS] Foundation 4.5 - 5.0', room='Lab 1', schedule='T2-T4-T6 (19h30)', price=3500000,
                  teacher_id=u_teacher_ielts.id, course_id=c_eng.id),
            Class(name='[IELTS] Speaking & Writing Master', room='P.VIP', schedule='Cuối tuần (Sáng)', price=4500000,
                  teacher_id=u_teacher_ielts.id, course_id=c_eng.id),
            Class(name='[Giao Tiếp] English for Business', room='P.101', schedule='T3-T5-T7 (18h00)', price=2500000,
                  teacher_id=u_teacher_ielts.id, course_id=c_eng.id),
            Class(name='[Kids] Tiếng Anh thiếu nhi K1', room='P.Kids', schedule='Cuối tuần (Chiều)', price=1200000,
                  teacher_id=u_teacher_toeic.id, course_id=c_eng.id),

            # --- NHÓM 2: TIẾNG NHẬT ---
            Class(name='[N5] Tiếng Nhật sơ cấp 1', room='P.201', schedule='T2-T4-T6 (18h00)', price=1600000,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id),
            Class(name='[N5] Tiếng Nhật sơ cấp 2', room='P.202', schedule='T3-T5-T7 (19h30)', price=1600000,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id),
            Class(name='[N4] Trung cấp & Kanji', room='P.201', schedule='T2-T4-T6 (19h30)', price=2200000,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id),
            Class(name='[N3] Luyện thi JLPT N3', room='P.VIP', schedule='Cuối tuần (Sáng)', price=3000000,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id),
            Class(name='[Kaiwa] Giao tiếp người bản xứ', room='Lab 2', schedule='T3-T5 (18h00)', price=2500000,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id),

            # --- NHÓM 3: TIẾNG HÀN ---
            Class(name='[Topik I] Hàn ngữ nhập môn', room='P.301', schedule='T2-T4-T6 (17h30)', price=1500000,
                  teacher_id=u_teacher_kor.id, course_id=c_kor.id),
            Class(name='[Topik II] Hàn ngữ sơ cấp 2', room='P.302', schedule='T3-T5-T7 (19h30)', price=1800000,
                  teacher_id=u_teacher_kor.id, course_id=c_kor.id),
            Class(name='[XKLĐ] Tiếng Hàn xuất khẩu lao động', room='Hội trường A', schedule='T2-T6 (Sáng)',
                  price=5000000, teacher_id=u_teacher_kor.id, course_id=c_kor.id),
            Class(name='[Giao Tiếp] Hàn ngữ du lịch', room='P.301', schedule='Cuối tuần (Chiều)', price=2000000,
                  teacher_id=u_teacher_kor.id, course_id=c_kor.id),

            # --- NHÓM 4: TIẾNG PHÁP ---
            Class(name='[A1] Tiếng Pháp cho người mới', room='P.401', schedule='T2-T4 (18h00)', price=2000000,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id),
            Class(name='[A2] Tiếng Pháp sơ cấp', room='P.401', schedule='T3-T5 (19h30)', price=2200000,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id),
            Class(name='[B1] Luyện thi DELF B1', room='P.VIP', schedule='Cuối tuần (Sáng)', price=4000000,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id),
            Class(name='[Giao Tiếp] Pháp ngữ văn phòng', room='Lab 1', schedule='T6-T7 (18h00)', price=3000000,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id),

            # --- LỚP BỔ SUNG CHO TRÒN 20 ---
            Class(name='[IELTS] Writing Task 1 & 2', room='Online Zoom', schedule='T7-CN (20h00)', price=2800000,
                  teacher_id=u_teacher_ielts.id, course_id=c_eng.id),
        ]

        db.session.add_all(classes)
        db.session.commit()

        # =================================================================
        # 4. TẠO QUY ĐỊNH
        # =================================================================
        if not Regulation.query.first():
            r1 = Regulation(name='PASSING_SCORE', value=5.0, description='Điểm trung bình chuẩn để ĐẬU')
            r2 = Regulation(name='MAX_STUDENTS', value=40, description='Sĩ số tối đa của một lớp')
            r3 = Regulation(name='MIN_AGE', value=18, description='Độ tuổi tối thiểu đăng ký học')
            db.session.add_all([r1, r2, r3])
            db.session.commit()

        print(f">>> ĐÃ TẠO THỦ CÔNG {len(classes)} LỚP HỌC THÀNH CÔNG!")