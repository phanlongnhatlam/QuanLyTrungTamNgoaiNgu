from models import User, Course, Class, ClassStatus  # Import models mới
from TrungTamNgoaiNgu import db  # Hoặc from saleapp import db tùy cấu trúc của bạn


# 1. Hàm load danh sách Khóa học (Để hiển thị lên Header/Tab)
# Thay thế cho load_categories cũ
def load_courses():
    return Course.query.all()


# 2. Hàm load danh sách Lớp học (Để hiển thị dưới trang chủ)
# Thay thế cho load_products cũ
def load_classes(course_id=None, kw=None):
    # Mặc định chỉ lấy các lớp đang MỞ
    query = Class.query.filter(Class.status == ClassStatus.OPEN)

    # Nếu có chọn Tab (course_id) thì lọc theo course_id
    if course_id:
        query = query.filter(Class.course_id == int(course_id))

    # Nếu có nhập từ khóa tìm kiếm
    if kw:
        query = query.filter(Class.name.contains(kw))

    return query.all()


# 3. Hàm lấy chi tiết lớp học (Thay cho get_product_by_id)
def get_class_by_id(class_id):
    return Class.query.get(class_id)
def get_user_by_id(user_id):
    # Tìm user trong database theo ID
    return User.query.get(user_id)