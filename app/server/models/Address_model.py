from pydantic import BaseModel, ConfigDict, Field


class CreateAddress(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    line: str = Field(min_length=1, max_length=300)
    city: str = Field(min_length=1, max_length=100)
    pincode: str = Field(min_length=1, max_length=20)
    phone: str = Field(min_length=1, max_length=20)
