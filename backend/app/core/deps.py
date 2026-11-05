"""
InvoiceFlow Pro - FastAPI Dependencies
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from databases import Database

from app.core.database import SessionLocal, get_database
from app.core.security import verify_token, get_token_subject
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.models.user import User, UserRole
from app.services.user_service import UserService

# Security scheme
security = HTTPBearer()


def get_db() -> Generator:
    """
    Get database session
    """
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


async def get_database_connection() -> Database:
    """
    Get async database connection
    """
    return await get_database()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    Get current authenticated user ID from JWT token
    """
    try:
        token = credentials.credentials
        user_id = get_token_subject(token)
        return int(user_id)
    except Exception as e:
        raise AuthenticationException(f"Could not validate credentials: {str(e)}")


async def get_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> User:
    """
    Get current authenticated user from database
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if not user:
        raise AuthenticationException("User not found")
    
    if not user.is_active:
        raise AuthenticationException("User account is disabled")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (alias for consistency)
    """
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            raise AuthorizationException(
                f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    
    return role_checker


def require_roles(*required_roles: UserRole):
    """
    Dependency factory to require one of multiple roles
    """
    async def roles_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            roles_str = ", ".join([role.value for role in required_roles])
            raise AuthorizationException(
                f"Access denied. Required roles: {roles_str}"
            )
        return current_user
    
    return roles_checker


async def get_admin_user(
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> User:
    """
    Get current user with admin role
    """
    return current_user


async def get_manager_or_admin_user(
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))
) -> User:
    """
    Get current user with manager or admin role
    """
    return current_user


def require_verified_user():
    """
    Dependency to require verified user
    """
    async def verified_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_verified:
            raise AuthorizationException("Email verification required")
        return current_user
    
    return verified_checker


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_id = get_token_subject(token)
        user_service = UserService(db)
        user = user_service.get_by_id(int(user_id))
        
        if user and user.is_active:
            return user
    except Exception:
        pass  # Invalid token, return None
    
    return None


class RateLimiter:
    """
    Simple rate limiting dependency
    """
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests = {}
    
    def __call__(self, user_id: int = Depends(get_current_user_id)):
        import time
        
        current_time = time.time()
        window_start = current_time - self.window_seconds
        
        # Clean old requests
        if user_id in self._requests:
            self._requests[user_id] = [
                req_time for req_time in self._requests[user_id]
                if req_time > window_start
            ]
        else:
            self._requests[user_id] = []
        
        # Check rate limit
        if len(self._requests[user_id]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds."
            )
        
        # Add current request
        self._requests[user_id].append(current_time)


# Rate limiting instances
standard_rate_limit = RateLimiter(max_requests=100, window_seconds=3600)  # 100 per hour
strict_rate_limit = RateLimiter(max_requests=10, window_seconds=300)  # 10 per 5 minutes


async def validate_invoice_access(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Validate that user has access to specific invoice
    """
    from app.services.invoice_service import InvoiceService
    
    invoice_service = InvoiceService(db)
    invoice = await invoice_service.get_by_id(invoice_id)
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Admin can access all invoices
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Users can only access their own invoices
    if invoice.user_id != current_user.id:
        raise AuthorizationException("Access denied to this invoice")
    
    return True


async def validate_customer_access(
    customer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    Validate that user has access to specific customer
    """
    from app.services.customer_service import CustomerService
    
    customer_service = CustomerService(db)
    customer = await customer_service.get_by_id(customer_id)
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Admin can access all customers
    if current_user.role == UserRole.ADMIN:
        return True
    
    # Users can only access their own customers
    if customer.user_id != current_user.id:
        raise AuthorizationException("Access denied to this customer")
    
    return True