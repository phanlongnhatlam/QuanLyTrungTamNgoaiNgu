document.addEventListener("DOMContentLoaded", function () {
    const confirmBtn = document.querySelector("#addColumnModal .btn-outline-success");
    if(confirmBtn) {
        confirmBtn.addEventListener("click", confirmAddColumn);
    }
});


function confirmAddColumn() {
    let nameInput = document.getElementById('newColName');
    let weightInput = document.getElementById('newColWeight');

    let name = nameInput.value.trim();
    let weight = parseFloat(weightInput.value);

    if (!name || isNaN(weight) || weight <= 0) {
        alert("Vui lòng nhập tên cột và hệ số hợp lệ!");
        return;
    }


    var modalElement = document.getElementById('addColumnModal');
    var modalInstance = bootstrap.Modal.getInstance(modalElement);
    if (modalInstance) modalInstance.hide();


    let tableHead = document.querySelector("#gradeTable thead tr");
    let avgTh = tableHead.lastElementChild;

    let newTh = document.createElement("th");
    newTh.className = "grade-col";
    newTh.setAttribute("data-name", name);
    newTh.setAttribute("data-weight", weight);
    newTh.innerHTML = `
        ${name} <br>
        <span class="badge bg-secondary">HS: ${weight}</span>
        <span class="text-danger fw-bold ms-2" style="cursor: pointer;" onclick="removeColumn(this)">&times;</span>
    `;

    tableHead.insertBefore(newTh, avgTh);


    document.querySelectorAll(".student-row").forEach(row => {
        let avgTd = row.lastElementChild;
        let newTd = document.createElement("td");
        newTd.className = "grade-cell";

        newTd.innerHTML = `<input type="number" class="form-control text-center score-input"
                                  step="0.1" min="0" max="10" placeholder="0">`;
        row.insertBefore(newTd, avgTd);
    });


    nameInput.value = "";
    weightInput.value = "";
}


function removeColumn(spanInfo) {
    if(!confirm("Bạn có chắc muốn xóa cột điểm này?")) return;

    let th = spanInfo.closest("th");
    let index = Array.from(th.parentNode.children).indexOf(th);

    th.remove();


    document.querySelectorAll(".student-row").forEach(row => {
        if(row.children[index]) row.children[index].remove();
    });
}


function saveAllGrades() {
    let totalWeight = 0;
    let headers = document.querySelectorAll(".grade-col");
    let colDefinitions = [];

    headers.forEach(th => {
        let w = parseFloat(th.getAttribute("data-weight"));
        totalWeight += w;

        colDefinitions.push({
            name: th.getAttribute("data-name"),
            weight: w
        });
    });

    if (totalWeight !== 100) {
        alert(`Lỗi trọng số: Tổng các hệ số hiện tại là ${totalWeight}. Tổng phải bằng 100! \n(Ví dụ: 15p(10) + GK(30) + CK(60) = 100)`);
        return;
    }

    let data = [];

    document.querySelectorAll(".student-row").forEach(row => {
        let enrollId = row.getAttribute("data-enroll-id");
        let scores = [];
        let inputs = row.querySelectorAll(".score-input");


        inputs.forEach((input, index) => {
            let val = input.value.trim();
            let numVal = 0;

            if (val !== "") {
                numVal = parseFloat(val);
            }

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