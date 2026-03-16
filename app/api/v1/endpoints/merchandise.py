"""Merchandise: products CRUD, orders CRUD, order status update."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_active_user, AdminOnly, Pagination
from app.core.responses import ok, paginated
from app.models.merchandise import Product, Order, OrderItem, OrderStatus
from app.schemas.schemas import ProductCreate, ProductUpdate, OrderCreate, OrderStatusIn

router = APIRouter(prefix="/merchandise", tags=["Merchandise"])


@router.get("/products", summary="List products")
async def list_products(pg: Pagination = Depends(), category: str | None = None,
                        db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    q = select(Product)
    if category:
        q = q.where(Product.category == category)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{
        "id": str(p.id), "name": p.name, "category": p.category, "price_kes": float(p.price_kes),
        "stock": p.stock, "tag": p.tag, "image_url": p.image_url,
    } for p in rows], total, pg.page, pg.per_page)


@router.post("/products", status_code=201, summary="Create product (admin)")
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    p = Product(**body.model_dump())
    db.add(p)
    await db.flush()
    return ok({"id": str(p.id), "name": p.name})


@router.patch("/products/{product_id}", summary="Update product")
async def update_product(product_id: UUID, body: ProductUpdate, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Product not found"})
    for f, v in body.model_dump(exclude_none=True).items():
        setattr(p, f, v)
    await db.flush()
    return ok({"id": str(p.id), "price_kes": float(p.price_kes), "stock": p.stock})


@router.delete("/products/{product_id}", status_code=204, summary="Delete product")
async def delete_product(product_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    p = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Product not found"})
    await db.delete(p)


@router.get("/orders", summary="List orders")
async def list_orders(pg: Pagination = Depends(), db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    total = (await db.execute(select(func.count()).select_from(Order))).scalar_one()
    rows = (await db.execute(select(Order).order_by(Order.placed_at.desc()).offset(pg.offset).limit(pg.per_page))).scalars().all()
    return paginated([{
        "id": str(o.id), "customer_id": str(o.customer_id),
        "total_kes": float(o.total_kes), "status": o.status.value,
        "placed_at": o.placed_at.isoformat(),
    } for o in rows], total, pg.page, pg.per_page)


@router.post("/orders", status_code=201, summary="Place order")
async def create_order(body: OrderCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_active_user)):
    total = 0.0
    order = Order(customer_id=current_user.id, total_kes=0)
    db.add(order)
    await db.flush()

    for item_in in body.items:
        p = (await db.execute(select(Product).where(Product.id == item_in.product_id))).scalar_one_or_none()
        if not p:
            raise HTTPException(404, {"code": "PRODUCT_NOT_FOUND", "message": f"Product {item_in.product_id} not found"})
        if p.stock < item_in.qty:
            raise HTTPException(422, {"code": "OUT_OF_STOCK", "message": f"{p.name} has insufficient stock"})
        p.stock -= item_in.qty
        line = OrderItem(order_id=order.id, product_id=p.id, qty=item_in.qty, unit_price_kes=p.price_kes)
        db.add(line)
        total += float(p.price_kes) * item_in.qty

    order.total_kes = total
    await db.flush()
    return ok({"order_id": str(order.id), "total_kes": total, "status": order.status.value})


@router.get("/orders/{order_id}", summary="Get order details")
async def get_order(order_id: UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_active_user)):
    o = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Order not found"})
    return ok({"id": str(o.id), "total_kes": float(o.total_kes), "status": o.status.value, "placed_at": o.placed_at.isoformat()})


@router.patch("/orders/{order_id}/status", summary="Update order status")
async def update_order_status(order_id: UUID, body: OrderStatusIn, db: AsyncSession = Depends(get_db), _=Depends(AdminOnly)):
    o = (await db.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "Order not found"})
    o.status = body.status
    await db.flush()
    return ok({"order_id": str(o.id), "status": o.status.value})
