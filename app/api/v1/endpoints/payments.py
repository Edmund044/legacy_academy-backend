# # routes/payments.py
# @router.post("/")
# def make_payment(data: dict, db: Session = Depends(get_db)):
#     payment = models.Payment(
#         order_id=data["order_id"],
#         amount=data["amount"],
#         method=data["method"],
#         status="success"
#     )

#     db.add(payment)

#     # update order
#     order = db.query(models.Order).get(data["order_id"])
#     order.status = "paid"

#     db.commit()
#     return payment