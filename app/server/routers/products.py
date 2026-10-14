from fastapi import APIRouter, HTTPException, Depends, Response, Query
from auth import require_admin, get_token_from_cookies
from database import get_db
from repositories.products import ProductRepository
from models.Product_model import AddProduct, UpdateProduct

router = APIRouter(prefix="/products", tags=["products"])

@router.get("")
def list_products(page: int = Query(1, ge=1),
                  page_size: int = Query(20, ge=1, le=100),
                  conn=Depends(get_db)):
    return ProductRepository(conn).list_products(page, page_size)

@router.post("", status_code=201)
def add_product(
    product: AddProduct,
    token: str = Depends(get_token_from_cookies),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    created_product = ProductRepository(conn).add_product(product, token)
    if "error" in created_product:
        raise HTTPException(status_code=403, detail=created_product["error"])
    return {
        "message": "Product added successfully",
        "product_id": created_product["id"],
        "product": product,
    }

@router.put("/{product_id}")
def update_product(product_id: int, product: UpdateProduct, admin=Depends(require_admin), conn=Depends(get_db), token: str = Depends(get_token_from_cookies)):
    service = ProductRepository(conn)
    result = service.update_product(product_id, product, token)
    if  "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return {"message": "Product updated successfully", "product": product}

@router.delete("/{product_id}")
def delete_product(product_id: int, admin=Depends(require_admin), conn=Depends(get_db), token: str = Depends(get_token_from_cookies)):
    service = ProductRepository(conn)
    result = service.delete_product(product_id, token)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return {"message": "Product deleted successfully"}
