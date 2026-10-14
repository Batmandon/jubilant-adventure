from fastapi import APIRouter, Depends, HTTPException, status

from auth import require_admin
from database import get_db
from models.Batch_model import CreateBatch, EditBatch
from repositories.batch import BatchRepository


router = APIRouter(
    prefix="/batches",
    tags=["batches"],
    dependencies=[Depends(require_admin)],
)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_batch(batch: CreateBatch, conn=Depends(get_db)):
    result = BatchRepository(conn).create_batch(batch)
    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return {"message": "Batch created successfully", "batch_id": result["id"]}


@router.patch("/{batch_id}")
def edit_batch(batch_id: int, batch: EditBatch, conn=Depends(get_db)):
    result = BatchRepository(conn).edit_batch(batch_id, batch)
    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return {"message": "Batch updated successfully"}


@router.delete("/{batch_id}")
def delete_batch(batch_id: int, conn=Depends(get_db)):
    result = BatchRepository(conn).delete_batch(batch_id)
    if "error" in result:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["error"],
        )
    return {"message": "Batch deleted successfully"}
