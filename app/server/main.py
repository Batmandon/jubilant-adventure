from fastapi import FastAPI, HTTPException, Depends, Response
from models.Product_model import AddProduct, UpdateProduct
from models.Authmodel import RegisterAccount, LoginCredentials
from database import get_db
from products import MedicineService
from auth import create_account, login_credentials

app = FastAPI()

@app.post("/register")
def register_user(user: RegisterAccount, conn=Depends(get_db)):
    result = create_account(user, conn)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/login")
def login_user(userlogin: LoginCredentials, response: Response, conn=Depends(get_db)):
    result = login_credentials(userlogin, conn, response)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

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