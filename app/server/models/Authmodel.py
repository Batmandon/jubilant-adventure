from pydantic import BaseModel, EmailStr, Field
from datetime import date

class RegisterAccount(BaseModel):
    first_name: str = Field(min_length=3, max_length=20)
    last_name: str = Field(min_length=3, max_length=20)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=8, max_length=20)

class LoginCredentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
