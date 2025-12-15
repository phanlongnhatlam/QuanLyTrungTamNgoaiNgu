from flask import render_template, request
from TrungTamNgoaiNgu import app, dao, login


@app.route("/")
def index():
    q = request.args.get('q')
    course_id = request.args.get('id')

    return render_template("index.html")

@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)

@app.context_processor
def common_attribute():
    return {
        'courses': dao.load_courses()
    }

if __name__ == '__main__':
    from TrungTamNgoaiNgu.admin import *
    app.run(debug=True)