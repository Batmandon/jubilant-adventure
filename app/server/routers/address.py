from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import get_db
from models.Address_model import CreateAddress
from repositories.address import AddressRepository

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(
    address: CreateAddress,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    result = AddressRepository(conn).create_address(user["sub"], address)
    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return {"message": "Address created successfully", "address": result}
