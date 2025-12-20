from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect
from TrungTamNgoaiNgu import app, db, dao
from TrungTamNgoaiNgu.models import User, Course, Class, UserRole, Enrollment, Regulation


class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN
    def inaccessible_callback(self, name, **kwargs):
        return redirect('/')

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')
    def is_accessible(self):
        return current_user.is_authenticated

class MyHomeView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html',
                           stats_revenue=dao.stats_revenue(),
                           stats_student=dao.stats_student_count_by_course(),
                           stats_quality=dao.stats_pass_rate_by_course(),
                           stats_month=dao.stats_revenue_by_month(year=2025))
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

admin = Admin(app, name="Quản trị trung tâm", index_view=MyHomeView())
admin.add_view(AuthenticatedModelView(User, db.session, name="Người dùng"))
admin.add_view(AuthenticatedModelView(Course, db.session, name="Khóa học"))
admin.add_view(AuthenticatedModelView(Class, db.session, name="Lớp học"))
admin.add_view(AuthenticatedModelView(Enrollment, db.session, name="Ghi danh"))
admin.add_view(LogoutView(name='Đăng xuất', endpoint='logout'))
admin.add_view(AuthenticatedModelView(Regulation, db.session, name="Quy định chung"))