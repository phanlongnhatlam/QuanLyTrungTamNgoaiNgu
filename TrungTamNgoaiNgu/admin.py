from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect
from TrungTamNgoaiNgu import app, db, dao
from TrungTamNgoaiNgu.models import User, Course, Class, UserRole, Enrollment


# 1. Class cha: Chỉ cho phép ADMIN truy cập
# (Theo slide trang 91 - AuthenticatedView) [cite: 1417]
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        # Nếu không phải Admin thì đá về trang chủ
        return redirect('/')

# 3. Class Logout (Đăng xuất ngay trong Admin)
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self):
        return current_user.is_authenticated

class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        # Lấy số liệu thống kê để hiện ngay trang chủ
        stats = dao.stats_revenue()
        return self.render('admin/stats.html', stats=stats) # Dùng luôn giao diện stats

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

# --- KHỞI TẠO ADMIN ---
# (Theo slide trang 76) [cite: 1182]
admin = Admin(app, name="Quản trị trung tâm",index_view=MyHomeView())# không chạy đc bootstrap3 hay 4 do flask admin quá cũ
# Thêm các trang quản lý dữ liệu (CRUD)
admin.add_view(AuthenticatedModelView(User, db.session, name="Người dùng"))
admin.add_view(AuthenticatedModelView(Course, db.session, name="Khóa học"))
admin.add_view(AuthenticatedModelView(Class, db.session, name="Lớp học"))
admin.add_view(AuthenticatedModelView(Enrollment, db.session, name="Ghi danh"))

# Thêm trang Thống kê & Đăng xuất
admin.add_view(LogoutView(name='Đăng xuất'))

# #Câu lệnh tạo dữ liệu giả trong mysql để test
# #-- 1. Đảm bảo đã có Khóa học Tiếng Anh (ID=1) và Tiếng Nhật (ID=2)
# -- (Nếu có rồi thì lệnh này sẽ bỏ qua, chưa có thì thêm mới)
# INSERT IGNORE INTO course (id, name, description) VALUES
# (1, 'Tiếng Anh Căn Bản', 'Dành cho người mất gốc'),
# (2, 'Tiếng Nhật Sơ Cấp', 'N5 - N4');
#
# -- 2. Tạo thêm 2 lớp học mới (Giả sử giáo viên ID=1 dạy)
# INSERT INTO class (id, name, room, schedule, max_students, start_date, status, course_id, teacher_id) VALUES
# (101, 'ENG-A1', 'P.101', 'T2-T4-T6', 20, NOW(), 'OPEN', 1, 1), -- Lớp Anh
# (102, 'JPN-N5', 'P.102', 'T3-T5-T7', 15, NOW(), 'OPEN', 2, 1); -- Lớp Nhật
#
# -- 3. Đăng ký học viên vào 2 lớp này (Giả sử lấy user ID 1, 2, 3 đi học)
# -- (Nếu ID user 1,2,3 không tồn tại, bạn hãy sửa thành ID user đang có trong bảng user của bạn)
# INSERT INTO enrollment (id, student_id, class_id, status, created_date) VALUES
# (1001, 1, 101, 'PAID', NOW()), -- User 1 học Anh
# (1002, 2, 101, 'PAID', NOW()), -- User 2 học Anh
# (1003, 3, 101, 'PAID', NOW()), -- User 3 học Anh
# (1004, 1, 102, 'PAID', NOW()), -- User 1 học thêm Nhật
# (1005, 2, 102, 'PAID', NOW()); -- User 2 học thêm Nhật
#
# -- 4. QUAN TRỌNG NHẤT: TẠO HÓA ĐƠN CHO CÁC LỚP VỪA THÊM
# INSERT INTO invoice (enrollment_id, amount, created_date, staff_id) VALUES
# (1001, 5000000, NOW(), 1), -- Thu 5 triệu tiền học Anh
# (1002, 5000000, NOW(), 1),
# (1003, 5000000, NOW(), 1),
# (1004, 3000000, NOW(), 1), -- Thu 3 triệu tiền học Nhật
# (1005, 3000000, NOW(), 1);