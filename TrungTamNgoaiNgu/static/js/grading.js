/* --- FILE: static/js/grading.js --- */

// 1. KHI LOAD TRANG: Gắn sự kiện cho nút Thêm cột
document.addEventListener("DOMContentLoaded", function () {
    const confirmBtn = document.querySelector("#addColumnModal .btn-outline-success");
    if(confirmBtn) {
        confirmBtn.addEventListener("click", confirmAddColumn);
    }
});

// 2. XỬ LÝ THÊM CỘT MỚI (Giao diện)
function confirmAddColumn() {
    let nameInput = document.getElementById('newColName');
    let weightInput = document.getElementById('newColWeight');

    let name = nameInput.value.trim();
    let weight = parseFloat(weightInput.value);

    if (!name || isNaN(weight) || weight <= 0) {
        alert("Vui lòng nhập tên cột và hệ số hợp lệ!");
        return;
    }

    // Ẩn Modal
    var modalElement = document.getElementById('addColumnModal');
    var modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) modalInstance.hide();

    // Thêm Header cột mới vào bảng
    let tableHead = document.querySelector("#gradeTable thead tr");
    let avgTh = tableHead.lastElementChild; // Cột Điểm TB (để chèn vào trước nó)

    let newTh = document.createElement("th");
    newTh.className = "grade-col"; // Class để nhận diện cột điểm
    newTh.setAttribute("data-name", name);
    newTh.setAttribute("data-weight", weight);
    newTh.innerHTML = `
        ${name} <br>
        <span class="badge bg-secondary">HS: ${weight}</span>
        <span class="text-danger fw-bold ms-2" style="cursor: pointer;" onclick="removeColumn(this)">&times;</span>
    `;

    tableHead.insertBefore(newTh, avgTh);

    // Thêm ô Input cho tất cả các dòng học viên
    document.querySelectorAll(".student-row").forEach(row => {
        let avgTd = row.lastElementChild;
        let newTd = document.createElement("td");
        newTd.className = "grade-cell";
        // Mặc định giá trị rỗng
        newTd.innerHTML = `<input type="number" class="form-control text-center score-input"
                                  step="0.1" min="0" max="10" placeholder="0">`;
        row.insertBefore(newTd, avgTd);
    });

    // Reset form
    nameInput.value = "";
    weightInput.value = "";
}

// 3. XÓA CỘT
function removeColumn(spanInfo) {
    if(!confirm("Bạn có chắc muốn xóa cột điểm này?")) return;

    let th = spanInfo.closest("th");
    let index = Array.from(th.parentNode.children).indexOf(th);

    th.remove(); // Xóa header

    // Xóa ô ở các dòng
    document.querySelectorAll(".student-row").forEach(row => {
        if(row.children[index]) row.children[index].remove();
    });
}

// 4. LƯU BẢNG ĐIỂM (Logic quan trọng đã sửa)
function saveAllGrades() {
    // --- BƯỚC A: KIỂM TRA TỔNG TRỌNG SỐ ---
    let totalWeight = 0;
    let headers = document.querySelectorAll(".grade-col"); // Lấy tất cả cột điểm
    let colDefinitions = []; // Lưu lại danh sách cột để dùng bên dưới

    headers.forEach(th => {
        let w = parseFloat(th.getAttribute("data-weight"));
        totalWeight += w;

        colDefinitions.push({
            name: th.getAttribute("data-name"),
            weight: w
        });
    });

    // Yêu cầu tổng trọng số phải là 100 (Code của bạn đang nhập số nguyên 10, 20... nên tổng là 100)
    // Nếu bạn nhập hệ số 0.1, 0.2 thì sửa số này thành 1.0
    if (totalWeight !== 100) {
        alert(`Lỗi trọng số: Tổng các hệ số hiện tại là ${totalWeight}. Tổng phải bằng 100! \n(Ví dụ: 15p(10) + GK(30) + CK(60) = 100)`);
        return; // Dừng lại, không lưu
    }

    // --- BƯỚC B: GOM DỮ LIỆU ---
    let data = [];

    document.querySelectorAll(".student-row").forEach(row => {
        let enrollId = row.getAttribute("data-enroll-id");
        let scores = [];
        let inputs = row.querySelectorAll(".score-input");

        // Duyệt qua từng ô input của học viên này
        inputs.forEach((input, index) => {
            let val = input.value.trim();
            let numVal = 0; // Mặc định là 0 nếu không nhập (ĐỂ CỘT KHÔNG BỊ MẤT)

            if (val !== "") {
                numVal = parseFloat(val);
            }

            // Lấy thông tin cột từ mảng colDefinitions đã tạo ở trên
            let colInfo = colDefinitions[index];

            scores.push({
                "name": colInfo.name,
                "value": numVal,
                "weight": colInfo.weight
            });
        });

        data.push({
            "enroll_id": enrollId,
            "scores": scores
        });
    });

    // --- BƯỚC C: GỬI VỀ SERVER ---
    if(!confirm("Xác nhận lưu bảng điểm?")) return;

    fetch('/api/save-grades', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.status === 200) {
            alert("Lưu thành công!");
            location.reload();
        } else {
            alert("Lỗi server: " + result.err_msg);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Không thể kết nối server!");
    });
}