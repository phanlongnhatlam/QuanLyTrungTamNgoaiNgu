from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)

# CẤU HÌNH KẾT NỐI DATABASE
# Lưu ý: Thay mật khẩu '123456' bằng mật khẩu của bạn (hoặc để trống nếu dùng XAMPP)
app.secret_key = "^%^&%^(*^^&^&^(*^&^&^&^" # Gõ gì cũng được cho bảo mật
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:abcd@localhost/trungtamngoaingu_db?charset=utf8mb4"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 10  # Số lượng hiển thị trên 1 trang (để sau này phân trang)

db = SQLAlchemy(app)
login = LoginManager(app)