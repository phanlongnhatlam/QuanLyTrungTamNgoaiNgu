import hashlib
from sqlalchemy import func, case, extract, or_
from datetime import datetime
from TrungTamNgoaiNgu.models import (User, Course, Class, Enrollment, Grade, GradeDetail, Attendance, Invoice,
                                     ClassStatus, EnrollmentStatus, UserRole)
from TrungTamNgoaiNgu import db, app



def load_courses():
    return Course.query.all()


def load_classes(course_id=None, kw=None, page=1):
    query = Class.query.filter(Class.status == ClassStatus.OPEN)

    if course_id:
        query = query.filter(Class.course_id == int(course_id))
    if kw:
        query = query.filter(Class.name.contains(kw))

    if page:
        page = int(page)
        size = app.config["PAGE_SIZE"]
        start = (page - 1) * size
        query = query.slice(start, start + size)
    return query.all()



def count_classes(course_id=None, kw=None):
    query = Class.query.filter(Class.status == ClassStatus.OPEN)

    if course_id:
        query = query.filter(Class.course_id == int(course_id))
    if kw:
        query = query.filter(Class.name.contains(kw))

    return query.count()

def get_class_by_id(class_id):
    return Class.query.get(class_id)

def get_user_by_id(user_id):
    return User.query.get(user_id)

def auth_user(username, password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username == username, User.password == password).first()

def add_user(name, username, password, avatar):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    u = User(name=name, username=username.strip(), password=password, avatar=avatar, role=UserRole.STUDENT)
    db.session.add(u)
    db.session.commit()
    return u

def count_classes_by_course():
    return db.session.query(Course.id, Course.name, func.count(Class.id)) \
        .join(Class, Class.course_id == Course.id, isouter=True) \
        .group_by(Course.id).all()



def save_cart_to_db(cart, user_id):
    if not cart: return False

    print(f"DEBUG: Bắt đầu lưu giỏ hàng cho User {user_id}")

    try:
        for c in cart.values():
            class_id = int(c['id'])
            print(f"DEBUG: Đang xử lý Class ID: {class_id}")

            exist = Enrollment.query.filter_by(student_id=user_id, class_id=class_id).first()
            if not exist:
                enroll = Enrollment(student_id=user_id, class_id=class_id, status=EnrollmentStatus.PENDING)
                db.session.add(enroll)
                print(f"DEBUG: Đã add vào session: Class {class_id}")
            else:
                print(f"DEBUG: Đã tồn tại, bỏ qua: Class {class_id}")

        db.session.commit()
        print("DEBUG: >>> COMMIT THÀNH CÔNG! <<<")
        return True

    except Exception as ex:
        print("LỖI LƯU DATABASE:", str(ex))
        db.session.rollback()
        return False




def get_unpaid_enrollments(keyword=None):

    query = Enrollment.query.filter(Enrollment.status == EnrollmentStatus.PENDING)

    count_pending = query.count()
    print(f"DEBUG >>> Số lượng phiếu PENDING trong DB: {count_pending}")


    query = query.outerjoin(User, Enrollment.student_id == User.id)

    if keyword:
        if keyword.isdigit():
            query = query.filter(or_(Enrollment.id == int(keyword), User.id == int(keyword)))
        else:
            query = query.filter(User.name.contains(keyword))

    results = query.all()


    print(f"DEBUG >>> Kết quả cuối cùng trả về: {len(results)} dòng")
    for e in results:
        student_name = e.student.name if e.student else "KHÔNG TÌM THẤY USER!"
        print(f"   ---> ID Phiếu: {e.id} | Student ID: {e.student_id} | Tên: {student_name}")

    return results


def pay_enrollment(enroll_id, cashier_id):
    try:
        enroll = Enrollment.query.get(enroll_id)

        if not enroll:
            print(f" Lỗi: Không tìm thấy Enrollment ID {enroll_id}")
            return False

        if enroll.status == EnrollmentStatus.PAID:
            print("️ Phiếu này đã thanh toán rồi!")
            return True

        enroll.status = EnrollmentStatus.PAID

        curr_class = Class.query.get(enroll.class_id)
        money = curr_class.price if curr_class else 0

        inv = Invoice(
            amount=money,
            created_date=datetime.now(),
            enrollment_id=enroll_id,
            cashier_id=cashier_id
        )

        db.session.add(inv)
        db.session.commit()

        print(f" Đã thanh toán thành công! Số tiền: {money}")
        return True

    except Exception as ex:
        db.session.rollback()
        print(" LỖI THANH TOÁN: " + str(ex))
        import traceback
        traceback.print_exc()
        return False




def get_students_by_class(class_id):
    return db.session.query(User.id, User.name, Enrollment.id.label('enroll_id')) \
        .join(Enrollment, User.id == Enrollment.student_id) \
        .filter(Enrollment.class_id == class_id).all()


def get_class_columns(class_id):
    existing_headers = db.session.query(GradeDetail.score_name, GradeDetail.weight) \
        .join(Grade, GradeDetail.grade_id == Grade.id) \
        .join(Enrollment, Grade.enrollment_id == Enrollment.id) \
        .filter(Enrollment.class_id == class_id) \
        .group_by(GradeDetail.score_name, GradeDetail.weight) \
        .order_by(GradeDetail.weight.asc()).all()

    if existing_headers:
        return [{'name': h.score_name, 'weight': int(h.weight)} for h in existing_headers]

    return [
        {'name': 'Miệng', 'weight': 10},
        {'name': '15 phút', 'weight': 20},
        {'name': 'Giữa kỳ', 'weight': 20},
        {'name': 'Cuối kỳ', 'weight': 50}
    ]


def save_grade_with_details(enroll_id, score_data_list):
    g = Grade.query.filter_by(enrollment_id=enroll_id).first()
    if not g:
        g = Grade(enrollment_id=enroll_id)
        db.session.add(g)
        db.session.flush()

    GradeDetail.query.filter_by(grade_id=g.id).delete()

    total_score = 0
    total_weight = 0

    for item in score_data_list:
        val = float(item['value'])
        wei = float(item['weight'])
        detail = GradeDetail(score_name=item['name'], score_value=val, weight=wei, grade_id=g.id)
        db.session.add(detail)
        total_score += val * wei
        total_weight += wei

    if total_weight > 0:
        g.average_score = round(total_score / total_weight, 2)
    else:
        g.average_score = 0.0

    g.result = "Đạt" if g.average_score >= 5.0 else "Không đạt"
    db.session.commit()


def get_students_with_grades(class_id):
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
            for d in grade.details:
                scores_map[d.score_name] = d.score_value
            if grade.average_score is not None: avg = grade.average_score
            if grade.result: res = grade.result

        result.append(
            {'id': s.id, 'name': s.name, 'enroll_id': s.enroll_id, 'scores': scores_map, 'avg': avg, 'result': res})
    return result


def get_attendance_today(class_id):
    today = datetime.now().date()
    return db.session.query(Enrollment.id.label('enroll_id'), User.name, User.id.label('student_id'),
                            Attendance.is_present) \
        .join(User, Enrollment.student_id == User.id) \
        .outerjoin(Attendance,
                   (Attendance.enrollment_id == Enrollment.id) & (func.date(Attendance.checkin_date) == today)) \
        .filter(Enrollment.class_id == class_id).all()


def save_daily_attendance(enroll_id, is_present):
    today = datetime.now().date()
    att = Attendance.query.filter(Attendance.enrollment_id == enroll_id,
                                  func.date(Attendance.checkin_date) == today).first()
    if att:
        att.is_present = is_present
    else:
        att = Attendance(enrollment_id=enroll_id, is_present=is_present, checkin_date=datetime.now())
        db.session.add(att)
    db.session.commit()




def stats_revenue():
    return db.session.query(Course.id, Course.name, func.sum(Invoice.amount)) \
        .join(Class, Class.course_id == Course.id) \
        .join(Enrollment, Enrollment.class_id == Class.id) \
        .join(Invoice, Invoice.enrollment_id == Enrollment.id) \
        .group_by(Course.id, Course.name).all()


def stats_student_count_by_course():
    return db.session.query(Course.id, Course.name, func.count(Enrollment.id)) \
        .join(Class, Class.course_id == Course.id) \
        .join(Enrollment, Enrollment.class_id == Class.id) \
        .group_by(Course.id, Course.name).all()


def stats_pass_rate_by_course():
    return db.session.query(
        Course.id, Course.name,
        func.sum(case((Grade.result == 'Đạt', 1), else_=0)),
        func.sum(case((Grade.result == 'Không đạt', 1), else_=0))
    ).join(Class, Class.course_id == Course.id) \
        .join(Enrollment, Enrollment.class_id == Class.id) \
        .join(Grade, Grade.enrollment_id == Enrollment.id) \
        .group_by(Course.id, Course.name).all()


def stats_revenue_by_month(year=2025):
    return db.session.query(func.extract('month', Invoice.created_date), func.sum(Invoice.amount)) \
        .filter(func.extract('year', Invoice.created_date) == year) \
        .group_by(func.extract('month', Invoice.created_date)) \
        .order_by(func.extract('month', Invoice.created_date)).all()