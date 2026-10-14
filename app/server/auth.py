from models.Authmodel import RegisterAccount, LoginCredentials
from database import get_db
from utils.utils import hash_password, verify_password
from services.jwt import create_access_token, create_refresh_token, decode_token
from fastapi import Response, Request, HTTPException, Depends
import os

IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Helperfunction~~~~~~~~~~~~~~~~~~~~~~~~~~~

def get_user(cur, email: str):
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    return cur.fetchone()

def get_token_from_cookies(request: Request):
    """Extract the access token from the request cookies."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token

def get_current_user(token: str = Depends(get_token_from_cookies)):
    payload = decode_token(token, "access")
    if payload is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return payload

def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~Auth Operations~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def create_account(Register: RegisterAccount, conn):
        with conn.cursor() as cur:

            if get_user(cur, Register.email):
                return {"error": "Account already exists"}

            hashed_password= hash_password(Register.password)

            cur.execute("INSERT INTO users (first_name, last_name, email, phone, password_hash)  VALUES (%s, %s, %s, %s, %s)", (Register.first_name, Register.last_name, Register.email, Register.phone, hashed_password))

            return {"Message": "Account Successfully Created"}

def login_credentials(userlogin: LoginCredentials, conn, response: Response):
    with conn.cursor() as cur:
        user = get_user(cur, userlogin.email)

        if not user or not verify_password(userlogin.password, user["password_hash"]):
            return {"error": "Invalid email or password"}

        token_data = {"sub": user["email"], "name": user["first_name"] + " " + user["last_name"], "role": user["role"]}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        response.set_cookie(
            key = "access_token",
            value = access_token,
            httponly = True,
            secure = IS_PRODUCTION, # True for production false for local
            samesite = "none" if IS_PRODUCTION else "lax", # none for production lax for local
            max_age = 1800
            # domain = "127.0.0.1",
        )
        response.set_cookie(
            key = "refresh_token",
            value = refresh_token,
            httponly = True,
            secure = IS_PRODUCTION,
            samesite = "none" if IS_PRODUCTION else "lax",
            max_age = 604800
            # domain = "127.0.0.1",
        )

        return {"message": "Login successful", "name": user["first_name"] + " " + user["last_name"]}


def get_user_info_from_request(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        return {"error": "Not authenticated"}

    payload = decode_token(token, "access")

    if "error" in payload:
        return payload

    return {
        "email": payload.get("sub"),
        "name": payload.get("name"),
        "role": payload.get("role")
    }

def get_user_info_refresh_token (request: Request, response: Response):
    token = request.cookies.get("refresh_token")

    if not token:
        return{"error": "Please Log IN"}

    payload = decode_token(token, "refresh")

    if "error" in payload:
        return payload

    email = payload.get("sub")
    with get_db() as db:
        user = get_user(db, email)

        if not user:
            return {"error": "user not found"}

    access_token =  create_access_token({
        "sub": user["email"],
        "name": user["first_name"] + " " + user["last_name"],
        "role": user["role"]
    })

    response.set_cookie(
        key = "access_token",
        value = access_token,
        httponly = True,
        secure = True,
        samesite = "none",
        max_age = 1800

    )

def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="none",
        secure=True
    )

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="none",
        secure=True
    )
    return {"message": "Logged out successfully"}
