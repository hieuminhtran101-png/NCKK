from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserOut
from app.core import auth_mongo as auth_core
from app.db.mongodb import get_db
from datetime import datetime
from typing import Dict

router = APIRouter()

@router.post('/auth/register', response_model=UserOut, status_code=201)
def register(payload: UserCreate):
    try:
        db = get_db()
        # Check email exists
        user = db["users"].find_one({"email": payload.email})
        if user is not None:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user with hashed password
        salt = auth_core.generate_salt()
        hash_result = auth_core.hash_password(payload.password, salt)
        hashed_pwd = hash_result["hashed_password"]
        print(f"DEBUG Register: Salt={salt[:10]}..., Hash={hashed_pwd[:10]}...")
        
        user_data = {
            "email": payload.email,
            "password_hash": hashed_pwd,
            "password_salt": salt,
            "full_name": payload.full_name,
            "role": getattr(payload, 'role', 'user'),
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = db["users"].insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        
        return UserOut(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            created_at=user_data["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Registration error: {str(e)}")


@router.post('/auth/login')
def login(payload: UserCreate):
    try:
        db = get_db()
        user = db["users"].find_one({"email": payload.email})
        
        if user is None:
            raise HTTPException(status_code=401, detail='Invalid credentials')
        
        # Verify password
        pwd_valid = auth_core.verify_password(payload.password, user["password_salt"], user["password_hash"])
        print(f"DEBUG: Email={payload.email}, Salt={user['password_salt'][:10]}..., Hash={user['password_hash'][:10]}..., Valid={pwd_valid}")
        if not pwd_valid:
            raise HTTPException(status_code=401, detail='Invalid credentials')
        
        # Create JWT token
        token = auth_core.create_access_token(str(user["_id"]), user.get("role", "user"))
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail='Invalid credentials')