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


# FILE: dao.py

def get_unpaid_invoice(keyword=None):
    # 1. Lấy tất cả hóa đơn chưa thanh toán
    query = Invoice.query.filter(Invoice.status == False)

    # 2. [QUAN TRỌNG] Đổi .join thành .outerjoin
    # Để nếu User bị xóa mất thì Hóa đơn vẫn hiện ra
    query = query.outerjoin(Invoice.user)

    if keyword:
        # Logic tìm kiếm
        if keyword.isdigit():
            # Tìm theo ID Invoice HOẶC ID User
            query = query.filter(or_(
                Invoice.id == int(keyword),
                User.id == int(keyword)
            ))
        else:
            query = query.filter(User.name.contains(keyword))

    # In ra màn hình console để kiểm tra xem tìm được mấy cái
    results = query.all()
    print(f"========================================")
    print(f"DEBUG: Tìm thấy {len(results)} hóa đơn trong Database")
    print(f"========================================")

    return results


# --- HÀM 2: XỬ LÝ THANH TOÁN (THU TIỀN) ---
def pay_invoice(receipt_id):
    r = Invoice.query.get(receipt_id)
    if r:
        r.status = True  # Cập nhật trạng thái thành Đã thanh toán
        db.session.commit()
        return True
    return False


def add_invoice(cart, user_id):
    if cart:
        try:
            total_amount = 0
            # Tính tổng tiền từ giỏ hàng
            for c in cart.values():
                total_amount += c['price'] * c['quantity']

            # Tạo đối tượng Invoice mới
            # Lưu ý: enrollment_id mình để mặc định là None (nullable=True)
            # vì lúc này chỉ mới tạo hóa đơn, chưa xử lý xếp lớp
            inv = Invoice(user_id=user_id, amount=total_amount, status=False)

            db.session.add(inv)
            db.session.commit()

            print(">>> ĐÃ LƯU HÓA ĐƠN THÀNH CÔNG!")
            return True
        except Exception as ex:
            print("Lỗi lưu hóa đơn:", str(ex))
            return False
    return False