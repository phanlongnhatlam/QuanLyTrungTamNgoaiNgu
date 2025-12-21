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

class ClassLevel(enum.Enum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3

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
    level = Column(Enum(ClassLevel), default=ClassLevel.BEGINNER)

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

    # Dùng db.Column và db.Integer (có chữ db. đằng trước)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    value = db.Column(db.Float, default=0)
    description = db.Column(db.String(200))

    def __str__(self):
        return self.name  # Nên return name để dễ nhìn hơn description

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
        # =================================================================
        # 3. TẠO CLASS (CẬP NHẬT THÊM LEVEL VÀ GIÁ CHUẨN)
        # =================================================================
        classes = [
            # --- TIẾNG ANH ---
            Class(name='[Intermediate] Luyện thi TOEIC cấp tốc 550+', room='P.101', schedule='T2-T4-T6 (17h30)',
                  price=2500000, level=ClassLevel.INTERMEDIATE,
                  teacher_id=u_teacher_toeic.id, course_id=c_eng.id,
                  image="https://th.bing.com/th/id/OIP.A728vC7i8nn0yksXxn6lcQHaE5?w=269&h=183&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Beginner] Tiếng Anh Basic cho người mất gốc', room='P.102', schedule='T3-T5-T7 (19h30)',
                  price=1500000, level=ClassLevel.BEGINNER,
                  teacher_id=u_teacher_toeic.id, course_id=c_eng.id,
                  image="https://th.bing.com/th/id/OIP.A728vC7i8nn0yksXxn6lcQHaE5?w=269&h=183&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Advanced] IELTS Foundation (Band 4.5 - 5.0)', room='Lab 1', schedule='T2-T4-T6 (19h30)',
                  price=3500000, level=ClassLevel.ADVANCED,
                  teacher_id=u_teacher_ielts.id, course_id=c_eng.id,
                  image="https://th.bing.com/th/id/OIP.WEEqdxMeKYQMhT4ZughsNAHaEK?w=275&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # --- TIẾNG NHẬT ---
            Class(name='[Beginner] Tiếng Nhật sơ cấp 1 (N5)', room='P.201', schedule='T2-T4-T6 (18h00)',
                  price=1500000, level=ClassLevel.BEGINNER,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id,
                  image="https://th.bing.com/th/id/OIP.cRTUo9uXcFe0PAZVaKdBswHaE8?w=255&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Beginner] Tiếng Nhật sơ cấp 2 (N5)', room='P.202', schedule='T3-T5-T7 (19h30)',
                  price=1500000, level=ClassLevel.BEGINNER,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id,
                  image="https://th.bing.com/th/id/OIP.cRTUo9uXcFe0PAZVaKdBswHaE8?w=255&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Intermediate] Tiếng Nhật Trung cấp & Kanji (N4)', room='P.201', schedule='T2-T4-T6 (19h30)',
                  price=2500000, level=ClassLevel.INTERMEDIATE,
                  teacher_id=u_teacher_jap.id, course_id=c_jap.id,
                  image="https://th.bing.com/th/id/OIP.cRTUo9uXcFe0PAZVaKdBswHaE8?w=255&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # --- TIẾNG HÀN ---
            Class(name='[Beginner] Hàn ngữ nhập môn (Topik I)', room='P.301', schedule='T2-T4-T6 (17h30)',
                  price=1500000, level=ClassLevel.BEGINNER,
                  teacher_id=u_teacher_kor.id, course_id=c_kor.id,
                  image="https://th.bing.com/th/id/OIP.5XXJZtFh_5kURi4-TIMJbAHaFj?w=220&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Intermediate] Hàn ngữ sơ cấp 2 (Topik II)', room='P.302', schedule='T3-T5-T7 (19h30)',
                  price=2500000, level=ClassLevel.INTERMEDIATE,
                  teacher_id=u_teacher_kor.id, course_id=c_kor.id,
                  image="https://th.bing.com/th/id/OIP.5XXJZtFh_5kURi4-TIMJbAHaFj?w=220&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Advanced] Luyện thi Xuất khẩu lao động', room='Hội trường A', schedule='T2-T6 (Sáng)',
                  price=3500000, level=ClassLevel.ADVANCED,
                  teacher_id=u_teacher_kor.id, course_id=c_kor.id,
                  image="https://th.bing.com/th/id/OIP.5XXJZtFh_5kURi4-TIMJbAHaFj?w=220&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            # --- TIẾNG PHÁP ---
            Class(name='[Beginner] Tiếng Pháp cho người mới (A1)', room='P.401', schedule='T2-T4 (18h00)',
                  price=1500000, level=ClassLevel.BEGINNER,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id,
                  image="https://th.bing.com/th/id/OIP.wgUYAGe1p19elS9FnQW2OgHaE7?w=266&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Beginner] Tiếng Pháp sơ cấp (A2)', room='P.401', schedule='T3-T5 (19h30)',
                  price=1500000, level=ClassLevel.BEGINNER,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id,
                  image="https://th.bing.com/th/id/OIP.wgUYAGe1p19elS9FnQW2OgHaE7?w=266&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),

            Class(name='[Advanced] Luyện thi DELF B1', room='P.VIP', schedule='Cuối tuần (Sáng)',
                  price=3500000, level=ClassLevel.ADVANCED,
                  teacher_id=u_teacher_fra.id, course_id=c_fra.id,
                  image="https://th.bing.com/th/id/OIP.wgUYAGe1p19elS9FnQW2OgHaE7?w=266&h=180&c=7&r=0&o=7&cb=ucfimg2&dpr=1.5&pid=1.7&rm=3&ucfimg=1"),
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
            r4 = Regulation(name='FEE_BEGINNER', value=1500000, description='Học phí Cơ bản')
            r5 = Regulation(name='FEE_INTERMEDIATE', value=2500000, description='Học phí Trung cấp')
            r6 = Regulation(name='FEE_ADVANCED', value=3500000, description='Học phí Nâng cao')

            db.session.add_all([r1, r2, r3, r4, r5, r6])
            db.session.commit()

        print(f">>> ĐÃ TẠO DATABASE THÀNH CÔNG!")