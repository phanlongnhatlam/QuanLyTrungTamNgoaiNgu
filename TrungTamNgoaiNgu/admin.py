from TrungTamNgoaiNgu import app, db, dao
from TrungTamNgoaiNgu.models import Class, Course, User, Regulation, UserRole
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect


# 1. Class view chỉ dành cho Admin đã đăng nhập
class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN


# 2. Class view cho trang chủ Admin (Dashboard)
class MyAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        # Lấy số liệu thống kê từ DAO
        stats = dao.count_classes_by_course()
        # Gửi biến stats sang file HTML
        return self.render('admin/index.html', stats=stats)


# 3. Class đăng xuất
class LogoutView(BaseView):
    @expose("/")
    def index(self):
        logout_user()
        return redirect("/admin")

    def is_accessible(self):
        return current_user.is_authenticated


# 4. Khởi tạo Admin
admin = Admin(app=app,
              name="QUẢN TRỊ TRUNG TÂM",
              index_view=MyAdminIndexView())

# 5. Add các view
admin.add_view(AuthenticatedModelView(Course, db.session, name="Khóa học"))
admin.add_view(AuthenticatedModelView(User, db.session, name="Người dùng"))
admin.add_view(AuthenticatedModelView(Regulation, db.session, name="Quy định"))
admin.add_view(LogoutView(name="Đăng xuất"))