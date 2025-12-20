function addToCart(id,name,price){
    fetch('api/carts',{
        method: 'post',
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price
        }),
        headers: {
            "content-type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        let d = document.getElementsByClassName("cart-counter");
        for(let e of d){
            e.innerText = data.total_quantity;
        }
    })
}

function updateCart(productId, obj){
    fetch(`api/carts/${productId}`, {
        method: 'put',
        body: JSON.stringify({
            "quantity": parseInt(obj.value)
        }),
        headers: {
            "content-type": "application/json"
        }
    }).then(res => res.json()).then(data => {
        let d = document.getElementsByClassName("cart-counter");
        for(let e of d){
            e.innerText = data.total_quantity;
        }

        let d2 = document.getElementsByClassName("cart-amount");
        for(let e of d2){
            e.innerText = data.total_amount.toLocaleString("en");
        }
    })
}

function deleteCart(id){
    if(confirm("Co chac chan xoa?")===true){
        fetch(`api/carts/${id}`, {
            method: 'delete',
            headers: {
                "content-type": "application/json"
            }
        }).then(res => res.json()).then(data => {
            let d = document.getElementsByClassName("cart-counter");
            for(let e of d){
                e.innerText = data.total_quantity;
            }

            let d2 = document.getElementsByClassName("cart-amount");
            for(let e of d2){
                e.innerText = data.total_amount.toLocaleString("en");
            }

            let e = document.getElementById(`product${id}`);
            e.style.display = "none";
        })
    }
}

// 1. Phải truyền tham số enrollId vào hàm
function pay(enrollId) {
    if (confirm("Có chắc chắn thanh toán không?") === true) {

        fetch('/api/pay', { // Thêm dấu / ở đầu để chắc chắn đúng đường dẫn
            method: 'post',

            // 2. QUAN TRỌNG: Phải khai báo header để Server biết đây là JSON
            headers: {
                'Content-Type': 'application/json'
            },

            // 3. QUAN TRỌNG: Phải đóng gói cái ID gửi đi
            body: JSON.stringify({
                "enroll_id": enrollId
            })

        }).then(res => res.json()).then(data => {
            if (data.status === 200) {
                alert(data.msg); // Thông báo thành công
                location.reload();
            } else {
                // In ra lỗi nếu có (data.msg hoặc data.err_msg tùy code python trả về)
                alert(data.msg || data.err_msg);
            }
        }).catch(err => {
            console.error(err); // In lỗi ra console nếu mất mạng hoặc lỗi code
        });
    }
}
function checkout() {
    if (!confirm("Xác nhận đăng ký các lớp này?")) return;

    // Gọi vào route checkout
    fetch('/api/checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    }).then(res => res.json()).then(data => {
        if (data.status === 200) {
            alert(data.msg);
            location.reload();
        } else {
            alert(data.msg);
        }
    });
}