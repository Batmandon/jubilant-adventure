import logging

import psycopg
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from auth import require_admin
from database import get_db
from repositories.products import ProductRepository
from models.Product_model import AddProduct, UpdateProduct

router = APIRouter(prefix="/products", tags=["products"])
logger = logging.getLogger(__name__)

@router.get("")
def list_products(page: int = Query(1, ge=1),
                  page_size: int = Query(20, ge=1, le=100),
                  conn=Depends(get_db)):
    return ProductRepository(conn).list_products(page, page_size)

@router.get("/search")
def search_products(
    name: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Search name cannot be blank")
    result = ProductRepository(conn).search_products(name, page, page_size)
    if result["total"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No products found matching '{name}'.",
        )
    return result

@router.get("/{product_id}/details")
def get_product_details(
    product_id: int = Path(gt=0),
    conn=Depends(get_db),
):
    try:
        product = ProductRepository(conn).get_product_details(product_id)
    except psycopg.Error:
        logger.exception("get_product_details failed")
        raise HTTPException(
            status_code=500,
            detail="Could not fetch product details.",
        )

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product

@router.post("", status_code=201)
def add_product(
    product: AddProduct, admin=Depends(require_admin), conn=Depends(get_db),
):
    created_product = ProductRepository(conn).add_product(product)
    if "error" in created_product:
        raise HTTPException(status_code=403, detail=created_product["error"])
    return {
        "message": "Product added successfully",
        "product_id": created_product["id"],
        "product": product,
    }

@router.put("/{product_id}")
def update_product(product_id: int, product: UpdateProduct, admin=Depends(require_admin), conn=Depends(get_db)):
    service = ProductRepository(conn)
    result = service.update_product(product_id, product)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"message": "Product updated successfully", "product": product}

@router.delete("/{product_id}")
def delete_product(product_id: int, admin=Depends(require_admin), conn=Depends(get_db)):
    service = ProductRepository(conn)
    result = service.delete_product(product_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return {"message": "Product deleted successfully"}
