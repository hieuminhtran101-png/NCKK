# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.security import decode_access_token
 
bearer_scheme = HTTPBearer()
 
 
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """
    Dependency dùng chung cho mọi route cần xác thực.
    Trả về student_id lấy từ JWT.
 
    Dùng:
        @router.get("/something")
        def my_route(student_id: str = Depends(get_current_user)):
            ...
    """
    token      = credentials.credentials
    student_id = decode_access_token(token)
 
    if not student_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return student_id