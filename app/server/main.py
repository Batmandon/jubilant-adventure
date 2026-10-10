from fastapi import FastAPI, Depends
from models.Product_model import AddProduct, UpdateProduct
from models.Authmodel import User
from products import MedicineService
from database import get_db

app = FastAPI()

@app.post("/register")
def register_user(user: User):
    # Implementation for user registration
    pass

@app.post("/products")
def add_product(product: AddProduct, conn=Depends(get_db)):
    service = MedicineService(conn)
    service.add_product(product)
    return {"message": "Product added successfully", "product": product}

@app.put("/products/{product_id}")
def update_product(product_id: int, product: UpdateProduct, conn=Depends(get_db)):
    service = MedicineService(conn)
    service.update_product(product_id, product)
    return {"message": "Product updated successfully", "product": product}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, conn=Depends(get_db)):
    service = MedicineService(conn)
    service.delete_product(product_id)
    return {"message": "Product deleted successfully"}