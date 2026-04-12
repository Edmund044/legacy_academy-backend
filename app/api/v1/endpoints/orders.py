# routes/orders.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db import models

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/")
def create_order(order_data: dict, db: Session = Depends(get_db)):
    items = order_data["items"]
    
    total = sum(item["price"] for item in items)

    # sibling discount (example 10%)
    discount = 0
    if len(items) > 1:
        discount = total * 0.1

    final_amount = total - discount

    order = models.Order(
        parent_id=order_data["parent_id"],
        total_amount=total,
        discount_amount=discount,
        final_amount=final_amount,
        status="pending"
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order