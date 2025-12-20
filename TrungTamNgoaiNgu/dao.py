import hashlib
from sqlalchemy import func, case
from datetime import datetime


from TrungTamNgoaiNgu.models import User, Course, Class, ClassStatus, Enrollment, Grade, Invoice, Attendance, \
    GradeDetail  # Import models mới
from TrungTamNgoaiNgu import db  # Hoặc from saleapp import db tùy cấu trúc của bạn


# 1. Hàm load danh sách Khóa học (Để hiển thị lên Header/Tab)
# Thay thế cho load_categories cũ
def load_courses():
    return Course.query.all()


# 2. Hàm load danh sách Lớp học (Để hiển thị dưới trang chủ)
# Thay thế cho load_products cũ
def load_classes(course_id=None, kw=None):
    query = Class.query.filter(Class.status == ClassStatus.OPEN)

    # --- ĐOẠN QUAN TRỌNG NHẤT ---
    # Nếu controller gửi course_id xuống, thì chỉ lấy lớp thuộc course đó
    if course_id:
        query = query.filter(Class.course_id == int(course_id))
    # -----------------------------

    if kw:
        query = query.filter(Class.name.contains(kw))

    return query.all()


# 3. Hàm lấy chi tiết lớp học (Thay cho get_product_by_id)
def get_class_by_id(class_id):
    return Class.query.get(class_id)
def get_user_by_id(user_id):
    # Tìm user trong database theo ID
    return User.query.get(user_id)
#Lấy danh sách học viên theo lớp, giáo viên thao tác
def get_students_by_class(class_id):
    return db.session.query(User.id, User.name, Enrollment.id.label('enroll_id'))\
             .join(Enrollment, User.id == Enrollment.student_id)\
             .filter(Enrollment.class_id == class_id).all()
def auth_user(username,password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def add_user(name, username, password, avatar):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    u = User(name=name, username=username.strip(), password=password, avatar=avatar)
    db.session.add(u)
    db.session.commit()
    return u
#Lưu dòng dữ liệu điểm danh
def save_attendance_data(enroll_id, is_present):
    at = Attendance(enrollment_id=enroll_id, is_present=is_present)
    db.session.add(at)
    db.session.commit()


def save_grade_data(enroll_id, midterm, final):
    """Lưu hoặc cập nhật điểm số (Sử dụng bảng Grade)"""
    g = Grade.query.filter_by(enrollment_id=enroll_id).first()
    if not g:
        g = Grade(enrollment_id=enroll_id)
        db.session.add(g)

    g.midterm_score = midterm
    g.final_score = final
    # Tính điểm trung bình (giả sử hệ số 1-1)
    g.average_score = (float(midterm) + float(final)) / 2
    db.session.commit()

def get_class_columns(class_id):
    """
    SỬA LỖI: Cột đã xóa bị hiện lại.
    Logic mới:
    1. Kiểm tra xem trong DB đã có cấu hình cột nào cho lớp này chưa.
    2. Nếu CÓ: Lấy hoàn toàn từ DB (bỏ qua mặc định).
    3. Nếu KHÔNG: Lấy cấu hình mặc định.
    """
    # Query xem lớp này đã có cột điểm nào được lưu trong GradeDetail chưa
    # Join: Enrollment -> Grade -> GradeDetail
    existing_headers = db.session.query(GradeDetail.score_name, GradeDetail.weight) \
        .join(Grade, GradeDetail.grade_id == Grade.id) \
        .join(Enrollment, Grade.enrollment_id == Enrollment.id) \
        .filter(Enrollment.class_id == class_id) \
        .group_by(GradeDetail.score_name, GradeDetail.weight) \
        .order_by(GradeDetail.weight.asc()).all()  # Sắp xếp theo trọng số tăng dần cho đẹp

    # Nếu đã có dữ liệu trong DB -> Trả về danh sách trong DB
    if existing_headers:
        return [{'name': h.score_name, 'weight': int(h.weight)} for h in existing_headers]

    # Nếu chưa có (Lớp mới tinh) -> Trả về mặc định (Tổng = 100)
    return [
        {'name': 'Miệng', 'weight': 10},
        {'name': '15 phút', 'weight': 20},
        {'name': 'Giữa kỳ', 'weight': 20},
        {'name': 'Cuối kỳ', 'weight': 50}
    ]


def save_grade_with_details(enroll_id, score_data_list):
    """
    SỬA LỖI: Điểm TB không cập nhật.
    Logic: Sau khi lưu chi tiết, tính ngay điểm TB và update vào bảng Grade.
    """
    g = Grade.query.filter_by(enrollment_id=enroll_id).first()
    if not g:
        g = Grade(enrollment_id=enroll_id)
        db.session.add(g)
        db.session.flush()  # Để có g.id dùng bên dưới

    # 1. Xóa chi tiết cũ
    GradeDetail.query.filter_by(grade_id=g.id).delete()

    # 2. Lưu chi tiết mới và TÍNH TOÁN LUÔN
    total_score = 0
    total_weight = 0

    for item in score_data_list:
        val = float(item['value'])
        wei = float(item['weight'])

        detail = GradeDetail(
            score_name=item['name'],
            score_value=val,
            weight=wei,
            grade_id=g.id
        )
        db.session.add(detail)

        # Cộng dồn để tính TB
        total_score += val * wei
        total_weight += wei

    # 3. Cập nhật điểm TB vào bảng Grade
    if total_weight > 0:
        avg = total_score / total_weight
        g.average_score = round(avg, 2)
    else:
        g.average_score = 0.0

    # Cập nhật kết quả (Đạt/Không Đạt)
    if g.average_score >= 5.0:
        g.result = "Đạt"
    else:
        g.result = "Không đạt"

    db.session.commit()


def get_students_with_grades(class_id):
    """
    Hàm lấy dữ liệu hiển thị ra bảng
    """
    students = db.session.query(User.id, User.name, Enrollment.id.label('enroll_id')) \
        .join(Enrollment, User.id == Enrollment.student_id) \
        .filter(Enrollment.class_id == class_id).all()

    result = []
    for s in students:
        grade = Grade.query.filter_by(enrollment_id=s.enroll_id).first()
        scores_map = {}
        avg = 0.0
        res = "Chưa xét"

        if grade:
            # Lấy list chi tiết điểm
            for d in grade.details:
                scores_map[d.score_name] = d.score_value

            # Lấy điểm TB từ DB (vì hàm save đã tính rồi)
            if grade.average_score is not None:
                avg = grade.average_score

            if grade.result:
                res = grade.result

        result.append({
            'id': s.id,
            'name': s.name,
            'enroll_id': s.enroll_id,
            'scores': scores_map,
            'avg': avg,
            'result': res
        })
    return result


def get_attendance_today(class_id):
    """
    Lấy danh sách học viên và trạng thái điểm danh hôm nay.
    Dùng LEFT JOIN (outerjoin) để lấy cả những học viên chưa được điểm danh.
    """
    today = datetime.now().date()

    return db.session.query(Enrollment.id.label('enroll_id'),
                            User.name,
                            User.id.label('student_id'),
                            Attendance.is_present) \
        .join(User, Enrollment.student_id == User.id) \
        .outerjoin(Attendance,
                   (Attendance.enrollment_id == Enrollment.id) & (func.date(Attendance.checkin_date) == today)) \
        .filter(Enrollment.class_id == class_id).all()


def save_daily_attendance(enroll_id, is_present):
    """
    Lưu điểm danh:
    - Nếu đã có bản ghi hôm nay -> Cập nhật (Update)
    - Nếu chưa có -> Thêm mới (Insert)
    """
    today = datetime.now().date()

    # Tìm xem sinh viên này hôm nay đã được điểm danh chưa
    att = Attendance.query.filter(
        Attendance.enrollment_id == enroll_id,
        func.date(Attendance.checkin_date) == today
    ).first()

    if att:
        att.is_present = is_present  # Cập nhật trạng thái
    else:
        # Tạo mới
        att = Attendance(enrollment_id=enroll_id, is_present=is_present, checkin_date=datetime.now())
        db.session.add(att)

    db.session.commit()

#Thống kê báo cáo cho Admin
def stats_revenue():
    return db.session.query(Course.id, Course.name, func.sum(Invoice.amount))\
             .join(Class, Class.course_id == Course.id)\
             .join(Enrollment, Enrollment.class_id == Class.id)\
             .join(Invoice, Invoice.enrollment_id == Enrollment.id)\
             .group_by(Course.id, Course.name).all()


#""" Thống kê số lượng học viên theo từng khóa """
def stats_student_count_by_course():
    return db.session.query(Course.id, Course.name, func.count(Enrollment.id))\
             .join(Class, Class.course_id == Course.id)\
             .join(Enrollment, Enrollment.class_id == Class.id)\
             .group_by(Course.id, Course.name).all()

 #   """ Thống kê số lượng Đậu/Rớt theo khóa """
def stats_pass_rate_by_course():
    return db.session.query(
        Course.id,
        Course.name,
        func.sum(case((Grade.result == 'Đạt', 1), else_=0)),       # Cột 2: Số lượng Đậu
        func.sum(case((Grade.result == 'Không đạt', 1), else_=0))  # Cột 3: Số lượng Rớt
    ).join(Class, Class.course_id == Course.id)\
     .join(Enrollment, Enrollment.class_id == Class.id)\
     .join(Grade, Grade.enrollment_id == Enrollment.id)\
     .group_by(Course.id, Course.name).all()


# """ Thống kê doanh thu theo từng tháng trong năm """
def stats_revenue_by_month(year=2025):
    return db.session.query(
        func.extract('month', Invoice.created_date),
        func.sum(Invoice.amount)
    ).filter(func.extract('year', Invoice.created_date) == year)\
     .group_by(func.extract('month', Invoice.created_date))\
     .order_by(func.extract('month', Invoice.created_date)).all()