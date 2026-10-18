from fastapi import APIRouter, Depends, HTTPException, status, Query
from database import get_db
from models.Order_model import AddCartItem, PlaceOrder
from auth import get_current_user

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