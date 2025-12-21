from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect
from TrungTamNgoaiNgu import app, db, dao
from TrungTamNgoaiNgu.models import User, Course, Class, UserRole, Enrollment, Regulation, ClassLevel


class AuthenticatedModelView(ModelView):
    can_edit = True

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/')


# --- XỬ LÝ LỚP HỌC (Cho phép sửa giá) ---
class ClassModelView(AuthenticatedModelView):
    # 1. Thêm 'max_students' vào danh sách hiển thị
    column_list = ('name', 'level', 'price', 'max_students', 'course', 'teacher', 'room')

    # 2. Form nhập liệu (Giữ nguyên)
    form_columns = ('name', 'level', 'price', 'course', 'teacher', 'room', 'schedule',
                    'max_students', 'start_date', 'image', 'status')

    # 3. Việt hóa tên cột cho đẹp (Mới thêm)
    column_labels = {
        'name': 'Tên lớp',
        'level': 'Cấp độ',
        'price': 'Học phí',
        'max_students': 'Sĩ số',
        'course': 'Thuộc khóa',
        'teacher': 'Giáo viên',
        'room': 'Phòng',
        'schedule': 'Lịch học',
        'start_date': 'Ngày khai giảng',
        'image': 'Ảnh',
        'status': 'Trạng thái'
    }

    # 4. Logic tự động cập nhật giá (Giữ nguyên code cũ của bạn)
    def on_model_change(self, form, model, is_created):
        # Nếu không nhập giá -> Tự lấy theo quy định
        if not model.price:
            reg_name = 'FEE_BEGINNER'
            if model.level == ClassLevel.INTERMEDIATE:
                reg_name = 'FEE_INTERMEDIATE'
            elif model.level == ClassLevel.ADVANCED:
                reg_name = 'FEE_ADVANCED'

            r = Regulation.query.filter(Regulation.name == reg_name).first()
            if r:
                model.price = r.value

        # Nếu không nhập sĩ số -> Tự lấy theo quy định MAX_STUDENTS
        if not model.max_students:
            r_max = Regulation.query.filter(Regulation.name == 'MAX_STUDENTS').first()
            if r_max:
                model.max_students = int(r_max.value)

        return super().on_model_change(form, model, is_created)


# --- XỬ LÝ QUY ĐỊNH (Bật nút Sửa) ---
class RegulationModelView(AuthenticatedModelView):
    # --- CẤU HÌNH QUYỀN ---
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True



    # --- KHẮC PHỤC LỖI MẤT NÚT SỬA ---
    # Hãy tắt 2 dòng này đi (chuyển thành False).
    # Khi tắt Modal, hệ thống sẽ dùng đường link cơ bản -> Nút sửa sẽ Luôn Luôn Hiện.
    create_modal = False
    edit_modal = False

    column_list = ('name', 'value', 'description')
    form_columns = ('name', 'value', 'description')

    column_labels = {
        'name': 'Tên quy định',
        'value': 'Giá trị',
        'description': 'Mô tả'
    }

    def after_model_change(self, form, model, is_created):
        # 1. LOGIC CẬP NHẬT HỌC PHÍ (GIỮ NGUYÊN)
        level_to_update = None
        if model.name == 'FEE_BEGINNER':
            level_to_update = ClassLevel.BEGINNER
        elif model.name == 'FEE_INTERMEDIATE':
            level_to_update = ClassLevel.INTERMEDIATE
        elif model.name == 'FEE_ADVANCED':
            level_to_update = ClassLevel.ADVANCED

        if level_to_update:
            try:
                classes = Class.query.filter(Class.level == level_to_update).all()
                for c in classes:
                    c.price = model.value
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Lỗi cập nhật giá: {str(e)}")

        # 2. LOGIC MỚI: CẬP NHẬT SĨ SỐ (MAX_STUDENTS)
        if model.name == 'MAX_STUDENTS':
            try:
                # Lấy tất cả các lớp học
                all_classes = Class.query.all()

                # Ép kiểu int vì sĩ số phải là số nguyên (Regulation.value là Float)
                new_max = int(model.value)

                for c in all_classes:
                    c.max_students = new_max

                db.session.commit()
                print(f"✅ ĐÃ CẬP NHẬT SĨ SỐ {new_max} CHO TOÀN BỘ LỚP HỌC")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Lỗi cập nhật sĩ số: {str(e)}")

        return super().after_model_change(form, model, is_created)

        return super().after_model_change(form, model, is_created)

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
        # --- ĐOẠN CODE KIỂM TRA (DEBUG) ---
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            # Lấy danh sách cột thực tế đang có trong database
            cols = [c['name'] for c in inspector.get_columns('regulation')]

            print("\n" + "=" * 40)
            print("DANH SÁCH CỘT TRONG BẢNG REGULATION:")
            print(cols)  # In ra danh sách cột

            if 'id' not in cols:
                print(">>> CẢNH BÁO: CHƯA CÓ CỘT 'id'. HÃY XÓA FILE DATABASE!")
            else:
                print(">>> OK: Đã có cột 'id'. Code Admin đã chuẩn.")
            print("=" * 40 + "\n")

        except Exception as e:
            print(f"Lỗi kiểm tra: {e}")
        # ----------------------------------

        return self.render('admin/stats.html',
                           stats_revenue=dao.stats_revenue(),
                           stats_student=dao.stats_student_count_by_course(),
                           stats_quality=dao.stats_pass_rate_by_course(),
                           stats_month=dao.stats_revenue_by_month(year=2025))

    def is_accessible(self):
        return True


# --- KHỞI TẠO ADMIN ---
admin = Admin(app, name="Quản trị trung tâm", index_view=MyHomeView())

# Add các View vào Admin
admin.add_view(AuthenticatedModelView(User, db.session, name="Người dùng"))
admin.add_view(AuthenticatedModelView(Course, db.session, name="Khóa học"))

# Sử dụng ClassModelView đã fix
admin.add_view(ClassModelView(Class, db.session, name="Lớp học"))

admin.add_view(AuthenticatedModelView(Enrollment, db.session, name="Ghi danh"))

# Sử dụng RegulationModelView để hiện nút sửa
admin.add_view(RegulationModelView(Regulation, db.session, name="Quy định chung"))

admin.add_view(LogoutView(name='Đăng xuất', endpoint='logout'))