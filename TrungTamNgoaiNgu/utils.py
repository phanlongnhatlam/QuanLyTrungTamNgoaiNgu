def count_cart(cart):
    total_amount = 0
    total_quantity = 0

    if cart:
        for c in cart.values():
            # Logic cũ: total_quantity += c['quantity']
            # Logic mới: Mỗi món là 1 đơn vị
            total_quantity += 1
            total_amount += c['price'] # Giá tiền thì vẫn cộng dồn

    return {
        "total_amount": total_amount,
        "total_quantity": total_quantity
    }