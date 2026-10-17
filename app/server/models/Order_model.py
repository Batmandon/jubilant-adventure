from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

class PaymentMethod(str, Enum):
    cod = "cod"
    pickup = "pickup"

class AddCartItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)

class UpdateCartItem(BaseModel):
    quantity: int = Field(ge=1, le=20)

class PlaceOrder(BaseModel):
    address_id: int
    payment_method: PaymentMethod