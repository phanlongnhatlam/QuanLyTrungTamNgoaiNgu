import math
import cloudinary.uploader
import cloudinary
from flask import render_template, request, redirect, flash,session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from TrungTamNgoaiNgu.models import Class, Enrollment, UserRole
from TrungTamNgoaiNgu import app, dao, login, db, utils, admin
from TrungTamNgoaiNgu.decoraters import anonymous_required




@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == UserRole.ADMIN:
            return redirect('/admin')
        elif current_user.role == UserRole.CASHIER:
            return redirect('/cashier')
        elif current_user.role == UserRole.TEACHER:
            return redirect('/teacher')
    kw = request.args.get('q')
    course_id = request.args.get('course_id')
    page = request.args.get('page', 1)

    classes = dao.load_classes(course_id=course_id, kw=kw, page=int(page))

    total = dao.count_classes(course_id=course_id, kw=kw)
    page_size = app.config['PAGE_SIZE']
    pages = math.ceil(total / page_size)

    return render_template("index.html", classes=classes, pages=pages)


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
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = dao.auth_user(username, password)

        if user:
            login_user(user)

            if user.role == UserRole.ADMIN:
                return redirect('/admin')
            elif user.role == UserRole.CASHIER:
                return redirect('/cashier')
            elif user.role == UserRole.TEACHER:
                return redirect('/teacher')
            else:
                next_page = request.args.get('next')
                return redirect(next_page if next_page else "/")
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template("login.html", err_msg=err_msg)


@app.route("/logout")
def logout_my_user():
    logout_user()
    return redirect('/login')


@app.route("/register", methods=['get', 'post'])
def register():
    err_msg = None
    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password == confirm:
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
            except Exception as ex:
                db.session.rollback()
                err_msg = f"Lỗi hệ thống: {str(ex)}"
        else:
            err_msg = "Mật khẩu không khớp!"

    return render_template("register.html", err_msg=err_msg)


@app.route("/login-admin", methods=["post"])
def login_admin_process():
    username = request.form.get("username")
    password = request.form.get("password")
    user = dao.auth_user(username, password)

    if user and user.role == UserRole.ADMIN:
        login_user(user)
        return redirect("/admin")
    else:
        return redirect("/admin")



@app.route('/cart')
def cart():
    return render_template('cart.html')


@app.route("/api/carts", methods=['post'])
def add_to_cart():

    cart = session.get('cart')
    if not cart:
        cart = {}

    id = str(request.json.get('id'))
    if id in cart:
        pass
    else:
        cart[id] = {
            "id": id,
            "name": request.json.get('name'),
            "price": request.json.get('price'),
            "quantity": 1
        }

    session['cart'] = cart
    return jsonify(utils.count_cart(cart=cart))


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




@app.route("/api/checkout", methods=['post'])
@login_required
def checkout():

    cart = session.get('cart')
    if not cart:
        return jsonify({'status': 400, 'msg': 'Giỏ hàng rỗng!'})

    if dao.save_cart_to_db(cart, current_user.id):
        del session['cart']
        return jsonify({'status': 200, 'msg': 'Đăng ký thành công! Vui lòng đến quầy để đóng tiền.'})

    return jsonify({'status': 500, 'msg': 'Lỗi khi lưu đơn hàng.'})


@app.route("/cashier")
@login_required
def cashier_index():
    if current_user.role != UserRole.CASHIER and current_user.role != UserRole.ADMIN:
        return redirect("/")
    kw = request.args.get("keyword")
    enrollments = dao.get_unpaid_enrollments(kw)
    return render_template("cashier/index.html", enrollments=enrollments)


@app.route('/api/pay', methods=['post'])
@login_required
def pay():

    if current_user.role != UserRole.CASHIER and current_user.role != UserRole.ADMIN:
        return jsonify({'status': 403, 'msg': 'Bạn không có quyền thực hiện hành động này!'})


    data = request.json
    enroll_id = data.get('enroll_id')
    if not enroll_id:
        return jsonify({'status': 400, 'msg': 'Thiếu mã phiếu ghi danh!'})

    if dao.pay_enrollment(enroll_id, current_user.id):
        return jsonify({"status": 200, "msg": "Thanh toán thành công"})

    return jsonify({"status": 500, "msg": "Lỗi hệ thống hoặc phiếu không hợp lệ"})

@app.route("/teacher")
@login_required
def teacher_index():
    if current_user.role != UserRole.TEACHER: return redirect("/")

    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template('teacher/index.html', classes=classes)


@app.route("/teacher/class/<int:class_id>/manage")
@login_required
def manage_class(class_id):
    if current_user.role != UserRole.TEACHER: return "Access Denied", 403

    c = dao.get_class_by_id(class_id)
    students = dao.get_students_with_grades(class_id)
    dynamic_columns = dao.get_class_columns(class_id)

    return render_template('teacher/class_management.html', clazz=c, students=students, columns=dynamic_columns)


@app.route("/teacher/class/<int:class_id>/attendance", methods=['get', 'post'])
@login_required
def attendance(class_id):
    if current_user.role != UserRole.TEACHER: return redirect("/")

    if request.method == 'POST':
        students = dao.get_students_by_class(class_id)
        for s in students:

            is_present = (request.form.get(f"att_{s.enroll_id}") == "on")
            dao.save_daily_attendance(s.enroll_id, is_present)
        return redirect(f"/teacher/class/{class_id}/attendance")

    return render_template('teacher/attendance.html',
                           clazz=dao.get_class_by_id(class_id),
                           students=dao.get_attendance_today(class_id))


@app.route("/api/save-grades", methods=['post'])
@login_required
def save_grades():

    if current_user.role != UserRole.TEACHER:
        return jsonify({"status": 403, "err_msg": "Không có quyền truy cập"})

    try:
        data = request.json
        for item in data:
            for s in item['scores']:
                try:

                    val = float(s['value'])
                    if val < 0 or val > 10:
                        return jsonify({
                            "status": 400,
                            "err_msg": f"Lỗi: Điểm '{s['name']}' là {val}. Điểm phải từ 0 đến 10."
                        })
                except ValueError:

                    return jsonify({"status": 400, "err_msg": "Dữ liệu điểm không hợp lệ (phải là số)."})


        for item in data:
            dao.save_grade_with_details(item['enroll_id'], item['scores'])


        return jsonify({"status": 200, "msg": "Lưu bảng điểm thành công!"})

    except Exception as ex:

        return jsonify({"status": 500, "err_msg": str(ex)})


@app.route("/classes/<int:class_id>")
def class_details(class_id):

    c = dao.get_class_by_id(class_id)
    return render_template('classes_details.html', prod=c)




@app.route('/register-class/<int:class_id>', methods=['POST'])
@login_required
def register_class(class_id):
    from sqlalchemy.exc import IntegrityError

    try:
        my_class = Class.query.get(class_id)

        if not my_class:
            flash('Lớp học không tồn tại!', 'danger')
            return redirect('/')

        existing = Enrollment.query.filter_by(student_id=current_user.id, class_id=class_id).first()
        if existing:
            flash(f'Bạn đã đăng ký lớp {my_class.name} rồi! Không thể đăng ký lại.', 'warning')
            return redirect('/')

        current_count = Enrollment.query.filter_by(class_id=class_id).count()

        if current_count >= my_class.max_students:
            flash(f'Thông báo: Lớp {my_class.name} đã ĐỦ SĨ SỐ (Full slot). Vui lòng chọn lớp khác!', 'danger')
            return redirect('/')


        new_enrollment = Enrollment(student_id=current_user.id, class_id=class_id)
        db.session.add(new_enrollment)
        db.session.commit()

        flash(f'Đăng ký thành công lớp: {my_class.name}!', 'success')

    except IntegrityError:
        db.session.rollback()
        flash(f'Hệ thống phát hiện bạn đã đăng ký lớp {my_class.name} rồi.', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Lỗi hệ thống: {str(e)}', 'danger')

    return redirect('/')
if __name__ == '__main__':
    app.run(debug=True)