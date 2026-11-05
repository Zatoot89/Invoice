"""
InvoiceFlow Pro - Users API Routes
"""
from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()
security = HTTPBearer()


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    company_name: Optional[str]
    is_active: bool
    role: str
    created_at: str
    updated_at: str


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


@router.get("/", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    token: str = Depends(security),
):
    """Get list of users (admin only)"""
    # TODO: Implement user listing with pagination and search
    mock_user = {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Example Corp",
        "is_active": True,
        "role": "user",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }
    
    return {
        "users": [mock_user],
        "total": 1,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, token: str = Depends(security)):
    """Get user by ID"""
    # TODO: Implement get user by ID
    return {
        "id": user_id,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company_name": "Example Corp",
        "is_active": True,
        "role": "user",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    token: str = Depends(security),
):
    """Update user by ID"""
    # TODO: Implement user update logic
    return {
        "id": user_id,
        "email": "user@example.com",
        "first_name": request.first_name or "John",
        "last_name": request.last_name or "Doe",
        "company_name": request.company_name or "Example Corp",
        "is_active": True,
        "role": "user",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@router.delete("/{user_id}")
async def delete_user(user_id: int, token: str = Depends(security)):
    """Delete user by ID (admin only)"""
    # TODO: Implement user deletion logic
    return {"message": f"User {user_id} deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(user_id: int, token: str = Depends(security)):
    """Activate user account (admin only)"""
    # TODO: Implement user activation logic
    return {"message": f"User {user_id} activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(user_id: int, token: str = Depends(security)):
    """Deactivate user account (admin only)"""
    # TODO: Implement user deactivation logic
    return {"message": f"User {user_id} deactivated successfully"}