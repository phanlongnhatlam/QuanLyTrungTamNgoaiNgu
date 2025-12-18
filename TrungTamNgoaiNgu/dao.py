import hashlib

from sqlalchemy import func

from TrungTamNgoaiNgu.models import User, Course, Class, ClassStatus  # Import models mới
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