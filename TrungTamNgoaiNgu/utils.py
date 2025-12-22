def count_cart(cart):
    total_amount = 0
    total_quantity = 0

    if cart:
        for c in cart.values():
            total_quantity += 1
            total_amount += c['price']

    return {
        "total_amount": total_amount,
        "total_quantity": total_quantity
    }