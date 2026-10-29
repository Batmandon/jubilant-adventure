from fastapi import APIRouter, Depends, HTTPException, Path, status, Query
from database import get_db
from models.Order_model import AddCartItem, PlaceOrder
from auth import get_current_user, require_admin
from repositories.admin_products import AdminProductRepository

from repositories.order import (
    AddressNotFound,
    EmptyCart,
    MissingBatchPrice,
    OrderRepository,
    OutOfStock,
    PrescriptionRequired,
)

import logging
import psycopg


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_cart_item(
    item: AddCartItem,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    repository = OrderRepository(conn)
    user_id = repository.get_user_id(user["sub"])
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
        )

    result = repository.add_cart_item(user_id, item.product_id, item.quantity)
    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return {"message": "Cart item added successfully", "cart_item": result}


@router.delete("/items/{product_id}")
def delete_cart_item(
    product_id: int = Path(gt=0),
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    repository = OrderRepository(conn)
    user_id = repository.get_user_id(user["sub"])
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
        )

    try:
        result = repository.delete_cart_item(user_id, product_id)
    except psycopg.Error:
        logger.exception("delete_cart_item failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not remove cart item.",
        )

    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return {"message": "Cart item removed successfully"}


@router.get("/items")
def get_cart_items(
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    try:
        repository = OrderRepository(conn)
        user_id = repository.get_user_id(user["sub"])
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user no longer exists.",
            )
        result = repository.get_cart_items(user_id)
    except OutOfStock as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Not enough stock for {e.product_name}",
        )
    except MissingBatchPrice as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Batch price is not set for {e.product_name}",
        )
    except psycopg.Error:
        logger.exception("get_cart_items failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch cart items.",
        )

    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return result



@router.post("", status_code=201)
def place_order(
    order: PlaceOrder,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    repository = OrderRepository(conn)
    user_id = repository.get_user_id(user["sub"])
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authenticated user no longer exists.")

    try:
        return repository.place_order(
            user_id=user_id,
            address_id=order.address_id,
            payment_method=order.payment_method.value,
        )
    except AddressNotFound:
        raise HTTPException(status_code=404, detail="Address not found")
    except EmptyCart:
        raise HTTPException(status_code=400, detail="Cart is empty")
    except OutOfStock as e:
        raise HTTPException(status_code=409, detail=f"Not enough stock for {e.product_name}")
    except MissingBatchPrice as e:
        raise HTTPException(status_code=409, detail=f"Batch price is not set for {e.product_name}")
    except PrescriptionRequired as e:
        raise HTTPException(status_code=400, detail=f"Prescription required for {e.product_name}")
    except psycopg.Error:
        logger.exception("place_order failed")     # details go to the log, not the user
        raise HTTPException(status_code=500, detail="Could not place order")


@router.get("")
def my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    repository = OrderRepository(conn)
    user_id = repository.get_user_id(user["sub"])
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authenticated user no longer exists.")

    try:
        return repository.list_orders(user_id, page, page_size)
    except psycopg.Error:
        logger.exception("list_orders failed")
        raise HTTPException(status_code=500, detail="Could not fetch orders")


@router.get("/{order_id}")
def get_order(
    order_id: int,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    repository = OrderRepository(conn)
    user_id = repository.get_user_id(user["sub"])
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authenticated user no longer exists.")

    try:
        order = repository.get_order(order_id, user_id)
    except psycopg.Error:
        logger.exception("get_order failed")
        raise HTTPException(status_code=500, detail="Could not fetch order")

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# ---------- Admin dashboard ----------
# Second router in this file (different prefix + admin-only). Include it in main.py too.
admin_router = APIRouter(
    prefix="/admin",
    tags=["admin-orders"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("/dashboard")
def dashboard(
    recent_limit: int = Query(10, ge=1, le=50),
    conn=Depends(get_db),
):
    try:
        orders = OrderRepository(conn)
        stats = orders.get_dashboard_stats()
        recent_orders = orders.list_recent_orders(recent_limit)
        counts = AdminProductRepository(conn).get_counts()
    except psycopg.Error:
        logger.exception("dashboard failed")
        raise HTTPException(status_code=500, detail="Could not load dashboard")

    return {**stats, **counts, "recent_orders": recent_orders}
