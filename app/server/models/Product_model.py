from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class ProductSaltInput(BaseModel):
    name: str = Field(max_length=100)
    strength: str = Field(max_length=20)

class AddProduct(BaseModel):
    name: str = Field(max_length=20)
    salts: list[ProductSaltInput] = Field(min_length=1)
    batch_no: str = Field(max_length=15)
    category: str = Field(max_length=30)
    strength: str = Field(max_length=20)
    form: str = Field(max_length=20)
    pack_size: str = Field(max_length=20)
    manufacturer: str = Field(max_length=100)
    scheduling: str = Field(max_length=10)
    gst_percent: float
    hsn_code: str = Field(max_length=20)
    storage_condition: str = Field(max_length=100)
    description: str = Field(max_length=500)
    image_url: str = Field(max_length=200)
    is_active: bool
    quantity: int = Field(ge=0)
    price: int = Field(ge=0)
    mrp: int = Field(ge=0)
    mfg_date: date
    expiry_date: date

class UpdateProduct(BaseModel):
    name: Optional[str] = Field(default=None, max_length=20)
    salts: Optional[list[ProductSaltInput]] = Field(default=None, min_length=1)
    batch_no: Optional[str] = Field(default=None, max_length=15)
    category: Optional[str] = Field(default=None, max_length=30)
    strength: Optional[str] = Field(default=None, max_length=20)
    form: Optional[str] = Field(default=None, max_length=20)
    pack_size: Optional[str] = Field(default=None, max_length=20)
    manufacturer: Optional[str] = Field(default=None, max_length=100)
    scheduling: Optional[str] = Field(default=None, max_length=10)
    gst_percent: Optional[float] = None
    hsn_code: Optional[str] = Field(default=None, max_length=20)
    storage_condition: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=200)
    is_active: Optional[bool] = None
    quantity: Optional[int] = Field(default=None, ge=0)
    price: Optional[int] = Field(default=None, ge=0)
    mrp: Optional[int] = Field(default=None, ge=0)
    mfg_date: Optional[date] = None
    expiry_date: Optional[date] = None
    
