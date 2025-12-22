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

function pay(enrollId) {
    if (confirm("Có chắc chắn thanh toán không?") === true) {

        fetch('/api/pay', {
            headers: {
                'Content-Type': 'application/json'
            },


            body: JSON.stringify({
                "enroll_id": enrollId
            })

        }).then(res => res.json()).then(data => {
            if (data.status === 200) {
                alert(data.msg); // Thông báo thành công
                location.reload();
            } else {

                alert(data.msg || data.err_msg);
            }
        }).catch(err => {
            console.error(err);
        });
    }
}
function checkout() {
    if (!confirm("Xác nhận đăng ký các lớp này?")) return;


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