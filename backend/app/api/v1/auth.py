"""
InvoiceFlow Pro - Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.core.deps import get_db, standard_rate_limit
from app.core.security import create_access_token, create_refresh_token, verify_token, REFRESH_TOKEN_TYPE
from app.core.exceptions import (
    AuthenticationException, 
    ValidationException, 
    ResourceAlreadyExistsException
)
from app.services.user_service import UserService
from app.models.user import UserRole, AuthProvider

router = APIRouter()
security = HTTPBearer()


# Pydantic models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    terms_accepted: bool = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


# Response models
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    company_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    auth_provider: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
    _: None = Depends(standard_rate_limit)
):
    """Register a new user"""
    if not request.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and conditions"
        )
    
    try:
        user_service = UserService(db)
        user = await user_service.create_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            company_name=request.company_name,
            role=UserRole.USER,
            auth_provider=AuthProvider.LOCAL,
            is_verified=False  # Requires email verification
        )
        
        # Create tokens
        access_token = create_access_token(
            subject=user.id,
            additional_claims={
                "role": user.role.value,
                "email": user.email
            }
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company_name": user.company_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            }
        )
        
    except ResourceAlreadyExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    _: None = Depends(standard_rate_limit)
):
    """Login user with email and password"""
    try:
        user_service = UserService(db)
        user = await user_service.authenticate_user(
            email=request.email,
            password=request.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create tokens with longer expiry if remember_me is True
        expires_minutes = 60 * 24 * 7 if request.remember_me else 30  # 7 days or 30 minutes
        
        access_token = create_access_token(
            subject=user.id,
            additional_claims={
                "role": user.role.value,
                "email": user.email
            }
        )
        refresh_token = create_refresh_token(subject=user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_minutes * 60,
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company_name": user.company_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token, REFRESH_TOKEN_TYPE)
        user_id = int(payload.get("sub"))
        
        # Get user
        user_service = UserService(db)
        user = await user_service.get_by_id(user_id)
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        access_token = create_access_token(
            subject=user.id,
            additional_claims={
                "role": user.role.value,
                "email": user.email
            }
        )
        new_refresh_token = create_refresh_token(subject=user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=30 * 60,  # 30 minutes
            user={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "company_name": user.company_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            }
        )
        
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout():
    """Logout user (token invalidation handled client-side)"""
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    _: None = Depends(standard_rate_limit)
):
    """Request password reset"""
    user_service = UserService(db)
    reset_token = await user_service.request_password_reset(request.email)
    
    # Always return success (don't reveal if email exists)
    return {
        "message": "If the email exists, a password reset link has been sent"
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    try:
        user_service = UserService(db)
        success = await user_service.reset_password(
            token=request.token,
            new_password=request.new_password
        )
        
        if success:
            return {"message": "Password reset successfully"}
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired reset token"
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user_service: UserService = Depends(lambda db=Depends(get_db): UserService(db)),
    current_user_id: int = Depends(lambda: 1)  # This should use proper auth dependency
):
    """Change user password"""
    try:
        success = await user_service.change_password(
            user_id=current_user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        
    except AuthenticationException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """Verify user email with token"""
    try:
        user_service = UserService(db)
        success = await user_service.verify_email(request.token)
        
        if success:
            return {"message": "Email verified successfully"}
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid or expired verification token"
    )


@router.post("/resend-verification")
async def resend_verification(
    request: ForgotPasswordRequest,  # Reuse email model
    db: Session = Depends(get_db),
    _: None = Depends(standard_rate_limit)
):
    """Resend email verification"""
    user_service = UserService(db)
    verification_token = await user_service.resend_verification_email(request.email)
    
    # Always return success (don't reveal if email exists)
    return {
        "message": "If the email exists and is not verified, a verification link has been sent"
    }


# OAuth routes (placeholder for now)
@router.get("/oauth/{provider}")
async def oauth_login(provider: str):
    """OAuth login with external provider"""
    # TODO: Implement OAuth flow
    supported_providers = ["google", "github", "microsoft"]
    
    if provider not in supported_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider. Supported: {', '.join(supported_providers)}"
        )
    
    return {
        "auth_url": f"https://{provider}.com/oauth/authorize?client_id=...",
        "state": "random_state_token"
    }


@router.post("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """OAuth callback handler"""
    # TODO: Implement OAuth callback processing
    return {
        "message": "OAuth callback received",
        "provider": provider,
        "code": code[:10] + "...",  # Don't log full code
        "state": state
    }