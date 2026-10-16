from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import get_db
from models.Order_model import AddCartItem
from repositories.order import OrderRepository

router = APIRouter(prefix="/cart", tags=["cart"])


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
