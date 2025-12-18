from sqlalchemy import or_
import hashlib
from sqlalchemy import func
from TrungTamNgoaiNgu.models import User, Course, Class, ClassStatus, Invoice  # Import models mới
from TrungTamNgoaiNgu import db  # Hoặc from saleapp import db tùy cấu trúc của bạn


def load_courses():
    return Course.query.all()

def load_classes(course_id=None, kw=None):
    query = Class.query.filter(Class.status == ClassStatus.OPEN)
    if course_id:
        query = query.filter(Class.course_id == int(course_id))
    if kw:
        query = query.filter(Class.name.contains(kw))
    return query.all()

def get_class_by_id(class_id):
    return Class.query.get(class_id)

def get_user_by_id(user_id):
    return User.query.get(user_id)

def auth_user(username,password):
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def add_user(name, username, password, avatar):
    password = hashlib.md5(password.strip().encode('utf-8')).hexdigest()
    u = User(name=name, username=username.strip(), password=password, avatar=avatar)
    db.session.add(u)
    db.session.commit()
    return u

def count_classes_by_course():
    # Câu lệnh SQL: SELECT c.id, c.name, COUNT(cl.id) FROM course c LEFT JOIN class cl ... GROUP BY c.id
    return db.session.query(Course.id, Course.name, func.count(Class.id))\
                     .join(Class, Class.course_id == Course.id, isouter=True)\
                     .group_by(Course.id).all()


def get_unpaid_receipts(keyword=None):
    # Lấy hóa đơn chưa thanh toán (giả sử cột status trong Receipt là False nghĩa là chưa trả)
    query = Invoice.query.filter(Invoice.status == False)

    if keyword:
        query = query.join(User)  # Kết nối bảng Receipt với User

        # Xử lý logic tìm kiếm thông minh
        if keyword.isdigit():
            # Nếu từ khóa là SỐ -> Tìm theo ID User
            query = query.filter(User.id == int(keyword))
        else:
            # Nếu từ khóa là CHỮ -> Tìm theo Tên hoặc Username
            query = query.filter(or_(
                User.name.contains(keyword),
                User.username.contains(keyword)
            ))

    return query.all()