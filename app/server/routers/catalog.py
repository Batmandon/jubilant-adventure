from fastapi import APIRouter, Depends, HTTPException, Path

from auth import require_admin
from database import get_db
from models.Catalog_model import (
    CreateBrand,
    CreateCategory,
    CreateManufacturer,
    CreateProductSalt,
    CreateSalt,
    CreateSupplier,
    EditBrand,
    EditCategory,
    EditManufacturer,
    EditProductSalt,
    EditSalt,
    EditSupplier,
)
from repositories.catalog import CatalogRepository

router = APIRouter(tags=["catalog"])


def _result_or_raise(result):
    if "status_code" in result:
        raise HTTPException(status_code=result["status_code"], detail=result["error"])
    return result


@router.get("/categories")
def list_categories(conn=Depends(get_db)):
    return CatalogRepository(conn).list_items("categories")


@router.post("/categories", status_code=201)
def create_category(item: CreateCategory, admin=Depends(require_admin), conn=Depends(get_db)):
    return _result_or_raise(CatalogRepository(conn).create_item("categories", item))


@router.patch("/categories/{item_id}")
def edit_category(
    item: EditCategory,
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).edit_item("categories", item_id, item))


@router.delete("/categories/{item_id}")
def delete_category(
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).delete_item("categories", item_id))


@router.get("/brands")
def list_brands(conn=Depends(get_db)):
    return CatalogRepository(conn).list_items("brands")


@router.post("/brands", status_code=201)
def create_brand(item: CreateBrand, admin=Depends(require_admin), conn=Depends(get_db)):
    return _result_or_raise(CatalogRepository(conn).create_item("brands", item))


@router.patch("/brands/{item_id}")
def edit_brand(
    item: EditBrand,
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).edit_item("brands", item_id, item))


@router.delete("/brands/{item_id}")
def delete_brand(
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).delete_item("brands", item_id))


@router.get("/manufacturers")
def list_manufacturers(conn=Depends(get_db)):
    return CatalogRepository(conn).list_items("manufacturers")


@router.post("/manufacturers", status_code=201)
def create_manufacturer(
    item: CreateManufacturer,
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).create_item("manufacturers", item))


@router.patch("/manufacturers/{item_id}")
def edit_manufacturer(
    item: EditManufacturer,
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).edit_item("manufacturers", item_id, item))


@router.delete("/manufacturers/{item_id}")
def delete_manufacturer(
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).delete_item("manufacturers", item_id))


@router.get("/suppliers")
def list_suppliers(conn=Depends(get_db)):
    return CatalogRepository(conn).list_items("suppliers")


@router.post("/suppliers", status_code=201)
def create_supplier(item: CreateSupplier, admin=Depends(require_admin), conn=Depends(get_db)):
    return _result_or_raise(CatalogRepository(conn).create_item("suppliers", item))


@router.patch("/suppliers/{item_id}")
def edit_supplier(
    item: EditSupplier,
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).edit_item("suppliers", item_id, item))


@router.delete("/suppliers/{item_id}")
def delete_supplier(
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).delete_item("suppliers", item_id))


@router.get("/salts")
def list_salts(conn=Depends(get_db)):
    return CatalogRepository(conn).list_items("salts")


@router.post("/salts", status_code=201)
def create_salt(item: CreateSalt, admin=Depends(require_admin), conn=Depends(get_db)):
    return _result_or_raise(CatalogRepository(conn).create_item("salts", item))


@router.patch("/salts/{item_id}")
def edit_salt(
    item: EditSalt,
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).edit_item("salts", item_id, item))


@router.delete("/salts/{item_id}")
def delete_salt(
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).delete_item("salts", item_id))


@router.get("/product-salts")
def list_product_salts(conn=Depends(get_db)):
    return CatalogRepository(conn).list_items("product_salts")


@router.post("/product-salts", status_code=201)
def create_product_salt(
    item: CreateProductSalt,
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).create_item("product_salts", item))


@router.patch("/product-salts/{item_id}")
def edit_product_salt(
    item: EditProductSalt,
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).edit_item("product_salts", item_id, item))


@router.delete("/product-salts/{item_id}")
def delete_product_salt(
    item_id: int = Path(ge=1),
    admin=Depends(require_admin),
    conn=Depends(get_db),
):
    return _result_or_raise(CatalogRepository(conn).delete_item("product_salts", item_id))
