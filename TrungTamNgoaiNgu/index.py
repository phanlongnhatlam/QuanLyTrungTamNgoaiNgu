import cloudinary
from flask import render_template, request, redirect, session, jsonify
from flask_login import login_user, logout_user

from TrungTamNgoaiNgu import app, dao, login, db, utils, admin
from TrungTamNgoaiNgu.decoraters import anonymous_required
from TrungTamNgoaiNgu.models import UserRole


@app.route("/")
def index():
    q = request.args.get('q')
    course_id = request.args.get('id')
    course_id = request.args.get('course_id')
    classes = dao.load_classes(course_id=course_id,kw=q)
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

        user = dao.auth_user(username, password)

        if user:
            login_user(user)
            # 1. Nếu là Admin -> Vào trang Admin
            if user.role == UserRole.ADMIN:
                return redirect('/admin')

            # 2. Nếu là Thu ngân -> Vào trang Thu tiền
            elif user.role == UserRole.STAFF:
                return redirect('/cashier')

            # 3. Nếu là Học viên/Giáo viên -> Về trang chủ (hoặc trang trước đó)
            else:
                next = request.args.get('next')
                return redirect(next if next else "/")
            next = request.args.get('next')
            return redirect(next if next else "/")
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
@app.route("/api/carts/<id>", methods=['put'])
def update_cart(id):
    cart = session.get('cart')

    if cart and  id in cart:
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
@app.route("/login-admin", methods=["post"])
def login_admin_process():
    username = request.form.get("username")
    password = request.form.get("password")

    # Gọi hàm xác thực user
    user = dao.auth_user(username, password)

    # Chỉ cho phép đăng nhập nếu user tồn tại VÀ là ADMIN
    if user and user.role == UserRole.ADMIN:
        login_user(user)
        return redirect("/admin")
    else:
        # Nếu sai thì quay lại trang admin nhưng báo lỗi (bạn có thể xử lý hiển thị lỗi sau)
        return redirect("/admin")


@app.route("/cashier")
def cashier_view():
    # Lấy từ khóa tìm kiếm từ ô nhập (keyword)
    keyword = request.args.get('keyword')

    # Gọi hàm trong DAO để tìm hóa đơn (nhớ import dao ở đầu file)
    invoice = dao.get_unpaid_invoice(keyword)

    return render_template("cashier.html", invoice=invoice)

if __name__ == '__main__':
    app.run(debug=True)
