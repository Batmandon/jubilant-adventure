from fastapi import FastAPI
from routers import products, expiry, auth_routes

app = FastAPI()

app.include_router(auth_routes.router)
app.include_router(products.router)
app.include_router(expiry.router)
