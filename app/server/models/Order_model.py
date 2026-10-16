from pydantic import BaseModel, ConfigDict, Field


class AddCartItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
