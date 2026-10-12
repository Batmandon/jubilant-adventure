from fastapi import FastAPI, HTTPException, Depends, Response
from models.Product_model import AddProduct, UpdateProduct
from models.Authmodel import RegisterAccount, LoginCredentials
from database import get_db
from routes.products import MedicineService
from auth import create_account, login_credentials, get_token_from_cookies

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
def add_product(product: AddProduct, conn=Depends(get_db), token: str = Depends(get_token_from_cookies)):
    service = MedicineService(conn)
    created_product = service.add_product(product, token)
    if "error" in created_product:
        raise HTTPException(status_code=403, detail=created_product["error"])
    return {
        "message": "Product added successfully",
        "product_id": created_product["id"],
        "product": product,
    }

@app.put("/products/{product_id}")
def update_product(product_id: int, product: UpdateProduct, conn=Depends(get_db), token: str = Depends(get_token_from_cookies)):
    service = MedicineService(conn)
    result = service.update_product(product_id, product, token)
    if  "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return {"message": "Product updated successfully", "product": product}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, conn=Depends(get_db), token: str = Depends(get_token_from_cookies)):
    service = MedicineService(conn)
    result = service.delete_product(product_id, token)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return {"message": "Product deleted successfully"}
