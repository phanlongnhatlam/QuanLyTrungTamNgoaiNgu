from TrungTamNgoaiNgu.models import Course, Class, User
from TrungTamNgoaiNgu import app

def load_courses():
    # Hàm này lấy danh sách tất cả khóa học
    return Course.query.all()

def load_classes(course_id=None):
    # Hàm lấy danh sách lớp, có thể lọc theo khóa học
    query = Class.query
    if course_id:
        query = query.filter(Class.course_id == course_id)
    return query.all()
def get_user_by_id(user_id):
    # Hàm này giúp Flask-Login lấy user từ ID lưu trong session
    return User.query.get(user_id)