from fastapi import FastAPI
from routers import products, expiry, auth_routes, batch, catalog

app = FastAPI()

app.include_router(auth_routes.router)
app.include_router(products.router)
app.include_router(expiry.router)
app.include_router(batch.router)
app.include_router(catalog.router)
