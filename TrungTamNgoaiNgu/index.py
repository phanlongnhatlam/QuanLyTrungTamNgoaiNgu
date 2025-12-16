import cloudinary
from flask import render_template, request, redirect, session, jsonify
from flask_login import login_user, logout_user

from TrungTamNgoaiNgu import app, dao, login, db, utils
from TrungTamNgoaiNgu.decoraters import anonymous_required


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

if __name__ == '__main__':
    app.run(debug=True)
