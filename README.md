# 🎓 HỆ THỐNG QUẢN LÝ TRUNG TÂM NGOẠI NGỮ
Đồ án môn học Công nghệ phần mềm - Website quản lý toàn diện cho trung tâm ngoại ngữ, bao gồm các chức năng đăng ký khóa học, thu học phí, quản lý điểm số và báo cáo thống kê.

👥 THÀNH VIÊN THỰC HIỆN
| 1 | **Trần Quốc Đồng** | 2351050034
| 2 | **Phan Long Nhật Lâm** | 2351050089
🚀 CÔNG NGHỆ SỬ DỤNG
### Backend
* **Ngôn ngữ:** Python 3.x
* **Framework:** Flask
* **ORM:** SQLAlchemy
* **Authentication:** Flask-Login
### Frontend
* **Giao diện:** HTML5, CSS3, Bootstrap 5
* **Template Engine:** Jinja2
* **Scripting:** JavaScript (Fetch API, Chart.js)
### Database & Tools
* **Cơ sở dữ liệu:** MySQL
* **Lưu trữ ảnh:** Cloudinary API
* **Quản lý mã nguồn:** Git/GitHub
## ✨ CHỨC NĂNG CHÍNH
### 1. Phân hệ Admin (Quản trị viên)
* Quản lý danh sách Khóa học, Lớp học, Giảng viên.
* **Xem báo cáo doanh thu:** Biểu đồ trực quan theo tháng/quý/năm.
* Thống kê số lượng học viên và tỷ lệ đậu/rớt.
### 2. Phân hệ Giáo viên (Teacher)
* Xem lịch dạy và danh sách lớp được phân công.
* **Nhập điểm điện tử:** Hỗ trợ nhập điểm thành phần (Miệng, 15', Giữa kỳ, Cuối kỳ). Hệ thống tự động tính điểm TB.
* **Điểm danh:** Ghi nhận trạng thái vắng/có mặt của học viên theo ngày.
### 3. Phân hệ Thu ngân (Cashier)
* Tra cứu thông tin học viên.
* Xem danh sách các phiếu ghi danh chưa đóng tiền (Pending).
* Thực hiện thanh toán và xuất hóa đơn điện tử.
### 4. Phân hệ Học viên (Student)
* Xem danh sách khóa học đang mở.
* **Đăng ký trực tuyến:** Thêm khóa học vào giỏ hàng và đăng ký nhanh.
* Xem thời khóa biểu và kết quả học tập cá nhân.
## 🛠 HƯỚNG DẪN CÀI ĐẶT

Bước 1: Clone dự án
```bash
git clone [https://github.com/username/QuanLyTrungTamNgoaiNgu.git](https://github.com/username/QuanLyTrungTamNgoaiNgu.git)
cd QuanLyTrungTamNgoaiNgu
### Bước 2: Cài đặt môi trường ảo
python -m venv venv
# Windows:
venv\Scripts\activate
# MacOS/Linux:
source venv/bin/activate
Bước 3: Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
Bước 4: Cấu hình Cơ sở dữ liệu
Mở MySQL Workbench, tạo database tên trungtamngoaingu_db.
Import file script SQL (nếu có) hoặc để SQLAlchemy tự tạo bảng.
Cấu hình chuỗi kết nối trong file __init__.py:
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost/trungtamngoaingu_db?charset=utf8mb4"
Bước 5: Chạy chương trình
python index.py
