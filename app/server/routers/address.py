from fastapi import APIRouter, Depends, HTTPException, status
import logging
import psycopg

from auth import get_current_user
from database import get_db
from models.Address_model import CreateAddress
from repositories.address import AddressRepository

router = APIRouter(prefix="/addresses", tags=["addresses"])
logger = logging.getLogger(__name__)


@router.get("")
def list_addresses(
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    try:
        result = AddressRepository(conn).list_addresses(user["sub"])
    except psycopg.Error:
        logger.exception("list_addresses failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch addresses.",
        )
    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return result


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
