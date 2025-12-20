import cloudinary.uploader
from flask import render_template, request, redirect, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from TrungTamNgoaiNgu import app, dao, login, db, utils, admin
from TrungTamNgoaiNgu.decoraters import anonymous_required
from TrungTamNgoaiNgu.models import UserRole, Class


@app.route("/")
def index():
    # --- ĐIỀU HƯỚNG THÔNG MINH ---
    # Nếu là Teacher -> Đẩy sang /teacher ngay lập tức  về trang chủ của giáo viên
    if current_user.is_authenticated and current_user.role == UserRole.TEACHER:
        return redirect("/teacher")

    #khi chạy lại server thì sẽ không bị vào trang index.html
    if current_user.is_authenticated and current_user.role == UserRole.ADMIN:
        return redirect("/admin")

    q = request.args.get('q')
    course_id = request.args.get('id')
    course_id = request.args.get('course_id')
    classes = dao.load_classes(course_id=course_id, kw=q)
    # pages = math.ceil(dao.count_product() / app.config["PAGE_SIZE"])
    return render_template("index.html", classes=classes)


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.context_processor
def common_attribute():
    return {
        'courses': dao.load_courses(),
        'stats_cart': utils.count_cart(session.get('cart'))
    }

@app.route("/login", methods=["get", "post"])
@anonymous_required
def login_my_user():
    err_msg = None
    if request.method.__eq__("POST"):
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_user(username, password)  # [cite: 1377, 1379]

        if user:
            login_user(user)  #

            # 1. Ưu tiên chuyển hướng theo tham số 'next' trên URL (nếu có)
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)

            # 2. Nếu không có 'next', kiểm tra vai trò để điều hướng
            if user.role == UserRole.TEACHER:  # [cite: 1401]
                return redirect("/teacher")  # Vào thẳng Dashboard giáo viên [cite: 1381]


            if user.role == UserRole.ADMIN:
                return redirect("/admin")  # Chuyển thẳng vào trang Admin
            # 3. Các vai trò khác về trang chủ
            return redirect("/")
        else:
            # Chỉ gán lỗi khi không tìm thấy user
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect('/login')


@app.route("/register", methods=['get', 'post'])
def register():
    err_msg = None
    if request.method.__eq__("POST"):
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password.__eq__(confirm):
            name = request.form.get('name')
            username = request.form.get("username")
            avatar = request.files.get('avatar')
            file_path = None

            if avatar:
                res = cloudinary.uploader.upload(avatar)
                file_path = res['secure_url']

            try:
                dao.add_user(name, username, password, avatar=file_path)
                return redirect('/login')
            except:
                db.session.rollback()
                err_msg = "Hệ thống đang bị lỗi! Vui lòng quay lại sau!"
        else:
            err_msg = "Mật khẩu không khớp!"

    return render_template("register.html", err_msg=err_msg)


@app.route("/teacher/class/<int:class_id>/attendance", methods=['get', 'post'])
@login_required
def attendance(class_id):
    # 1. Kiểm tra quyền giáo viên
    if current_user.role != UserRole.TEACHER:
        return redirect("/")

    # 2. Xử lý khi bấm nút LƯU (POST)
    if request.method == 'POST':
        # Lấy lại danh sách học viên để duyệt qua từng người
        students = dao.get_students_by_class(class_id)

        for s in students:
            # Trong HTML checkbox:
            # - Nếu tích: request.form.get('name') trả về "on"
            # - Nếu không tích: trả về None
            key = f"att_{s.enroll_id}"
            is_present = (request.form.get(key) == "on")

            # Gọi hàm DAO để lưu xuống DB
            dao.save_daily_attendance(s.enroll_id, is_present)

        # Lưu xong thì load lại trang chính nó để thấy kết quả
        return redirect(f"/teacher/class/{class_id}/attendance")

    # 3. Hiển thị giao diện (GET)
    clazz = dao.get_class_by_id(class_id)
    students = dao.get_attendance_today(class_id)

    return render_template('teacher/attendance.html', clazz=clazz, students=students)

@app.route("/teacher")
@login_required
def teacher_index():
    if current_user.role != UserRole.TEACHER:
        return redirect("/")

    # Lấy các lớp có teacher_id trùng với ID người dùng hiện tại
    # Bạn cần đảm bảo trong Class model có trường teacher_id
    classes = Class.query.filter_by(teacher_id=current_user.id).all()

    return render_template('teacher/index.html', classes=classes)


@app.route("/teacher/class/<int:class_id>/manage")
@login_required
def manage_class(class_id):
    if current_user.role != UserRole.TEACHER:
        return "Access Denied", 403

    c = dao.get_class_by_id(class_id)
    students = dao.get_students_with_grades(class_id)

    # Lấy các cột điểm (Mặc định + Đã lưu)
    dynamic_columns = dao.get_class_columns(class_id)

    return render_template('teacher/class_management.html',
                           clazz=c,
                           students=students,
                           columns=dynamic_columns)


@app.route("/api/save-grades", methods=['post'])
@login_required
def save_grades():
    if current_user.role != UserRole.TEACHER:
        return jsonify({"status": 403})

    data = request.json  # Nhận dữ liệu Map từ JS
    try:
        for item in data:
            dao.save_grade_with_details(item['enroll_id'], item['scores'])
        return jsonify({"status": 200})
    except Exception as ex:
        return jsonify({"status": 500, "err_msg": str(ex)})


@app.route("/api/carts/<id>", methods=['put'])
def update_cart(id):
    cart = session.get('cart')

    if cart and id in cart:
        cart[id]["quantity"] = int(request.json.get("quantity"))
        session['cart'] = cart

    return jsonify(utils.count_cart(cart=cart))


@app.route("/api/carts/<id>", methods=['delete'])
def delete_cart(id):
    cart = session.get('cart')

    if cart and id in cart:
        del cart[id]
        session['cart'] = cart

    return jsonify(utils.count_cart(cart=cart))


@app.route("/api/carts", methods=['post'])
def add_to_cart():
    cart = session.get('cart')

    if not cart:
        cart = {}

    id = str(request.json.get('id'))

    if id in cart:
        cart[id]["quantity"] += 1
    else:
        cart[id] = {
            "id": id,
            "name": request.json.get('name'),
            "price": request.json.get('price'),
            "quantity": 1
        }

    session['cart'] = cart

    print(session['cart'])

    return jsonify(utils.count_cart(cart=cart))


@app.route('/cart')
def cart():
    return render_template('cart.html')


if __name__ == '__main__':
    app.run(debug=True)
