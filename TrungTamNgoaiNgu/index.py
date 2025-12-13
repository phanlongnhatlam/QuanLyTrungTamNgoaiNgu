from flask import render_template, request
# LƯU Ý: Phải import thêm 'login' ở dòng dưới đây
from TrungTamNgoaiNgu import app, dao, login

# --- HÀM NÀY ĐỂ FIX LỖI "MISSING USER_LOADER" ---
@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)
# ------------------------------------------------

@app.route("/")
def index():
    courses = dao.load_courses()
    return render_template('index.html', courses=courses)

if __name__ == '__main__':
    from TrungTamNgoaiNgu.admin import *
    app.run(debug=True)