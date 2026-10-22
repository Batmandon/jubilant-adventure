from fastapi import APIRouter, HTTPException, Depends, Query
from auth import require_admin
from database import get_db
from repositories.products import ProductRepository
from models.Product_model import AddProduct, UpdateProduct

router = APIRouter(prefix="/products", tags=["products"])

@router.get("")
def list_products(page: int = Query(1, ge=1),
                  page_size: int = Query(20, ge=1, le=100),
                  conn=Depends(get_db)):
    return ProductRepository(conn).list_products(page, page_size)

@router.get("/search")
def get_product_by_name(
    name: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conn=Depends(get_db),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Search name cannot be blank")
    result = ProductRepository(conn).get_products_by_name(name, page, page_size)
    if result["total"] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No products found matching '{name}'.",
        )
    return result

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
