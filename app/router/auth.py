from fastapi import APIRouter,HTTPException
from app.schemas.auth import RegisterRequest,LoginRequest
from app.service.auth_service import register_user,login_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/regiter")
def register(data : RegisterRequest):
    user = register_user(data)
    if not user:
        raise HTTPException(status_code=400, detail="Mã sinh viên đã tồn tại")
    return{
        "id": user["id"],
        "student_id": user["student_id"],
        "full_name": user["full_name"]
    }

@router.post("/login")
def login(data: LoginRequest):
    user = login_user(data)
    
    if not user:
        raise HTTPException(status_code=401,detail="Mã sinh viên hoặc mật khẩu không hợp lệ nhé bro!" )
    return {
        "id": user["id"],
        "student_id": user["student_id"],
        "full_name": user["full_name"]
    }