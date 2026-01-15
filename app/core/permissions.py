"""
RBAC (Role-Based Access Control) decorators & utilities
"""

from functools import wraps
from fastapi import HTTPException, Header, Depends
from typing import Optional, List, Callable
from app.db.mongodb import get_db
from app.core.auth_mongo import verify_token, get_user_by_id, has_role, UserRole


async def get_current_user_from_header(x_user_id: Optional[str] = Header(None)):
    """Extract user từ X-User-Id header"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    return {"user_id": x_user_id}


async def get_current_user_from_token(authorization: Optional[str] = Header(None)):
    """Extract user từ JWT token trong Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return {
        "user_id": payload.get("user_id"),
        "role": payload.get("role")
    }


def require_auth(func: Callable) -> Callable:
    """Decorator: Require authentication (có X-User-Id hoặc Bearer token)"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Cố gắng lấy từ header
        x_user_id = kwargs.get("x_user_id") or kwargs.get("user_id")
        authorization = kwargs.get("authorization")
        
        if not x_user_id and not authorization:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Priority: Token > Header ID
        if authorization:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
        elif x_user_id:
            kwargs["user_id"] = x_user_id
            return await func(*args, **kwargs)
    
    return wrapper


def require_role(*roles: str) -> Callable:
    """Decorator: Require specific role(s)
    
    Usage:
    @require_role("admin")
    @require_role("admin", "instructor")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            db = get_db()
            user_role = kwargs.get("user_role") or kwargs.get("role")
            
            # Allow if admin
            if user_role == "admin":
                return await func(*args, **kwargs)
            
            # Check if user has required role
            if user_role not in roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Required roles: {', '.join(roles)}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class PermissionChecker:
    """Helper class để check permissions"""
    
    def __init__(self, required_role: Optional[str] = None, required_owner: bool = False):
        """
        Args:
            required_role: Role cần thiết (admin, instructor, user)
            required_owner: Check xem user có sở hữu resource không
        """
        self.required_role = required_role
        self.required_owner = required_owner
    
    async def __call__(self, user_id: str, user_role: str, resource_owner_id: str = None):
        """Check permission"""
        # Admin bypass all
        if user_role == "admin":
            return True
        
        # Check required role
        if self.required_role and user_role != self.required_role:
            if self.required_role != "admin" or user_role != "admin":
                return False
        
        # Check ownership
        if self.required_owner and resource_owner_id:
            if user_id != resource_owner_id:
                return False
        
        return True


# Predefined permission checkers
ADMIN_ONLY = PermissionChecker(required_role="admin")
INSTRUCTOR_OR_ADMIN = PermissionChecker(required_role="instructor")  # Admin automatically included
OWNER_OR_ADMIN = PermissionChecker(required_owner=True)
SELF_OR_ADMIN = PermissionChecker(required_owner=True)


async def check_admin(db, user_id: str) -> bool:
    """Check if user is admin"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    return user.get("role") == "admin"


async def check_instructor(db, user_id: str) -> bool:
    """Check if user is instructor"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    role = user.get("role", "user")
    return role in ["instructor", "admin"]


async def check_role(db, user_id: str, required_role: str) -> bool:
    """Generic role check"""
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    user_role = user.get("role", "user")
    
    # Admin has all roles
    if user_role == "admin":
        return True
    
    return user_role == required_role
