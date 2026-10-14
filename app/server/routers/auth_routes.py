from fastapi import APIRouter, HTTPException, Response, Depends
from auth import create_account, login_credentials
from database import get_db
from models.Authmodel import RegisterAccount, LoginCredentials

router = APIRouter(prefix="/auth_routes", tags=["authentication"])

@router.post("/register")
def register_user(user: RegisterAccount, conn=Depends(get_db)):
    result = create_account(user, conn)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/login")
def login_user(userlogin: LoginCredentials, response: Response, conn=Depends(get_db)):
    result = login_credentials(userlogin, conn, response)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result