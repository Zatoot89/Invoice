"""
InvoiceFlow Pro - User Service
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta

from app.models.user import User, UserRole, AuthProvider
from app.core.security import (
    get_password_hash, 
    verify_password, 
    generate_password_reset_token,
    generate_verification_token,
    PasswordValidator
)
from app.core.exceptions import (
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    ValidationException,
    AuthenticationException
)


class UserService:
    """
    Service class for user-related operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        company_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
        auth_provider: AuthProvider = AuthProvider.LOCAL,
        provider_id: Optional[str] = None,
        is_verified: bool = False
    ) -> User:
        """
        Create a new user
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ResourceAlreadyExistsException("User", email)
        
        # Validate password strength for local auth
        if auth_provider == AuthProvider.LOCAL:
            is_valid, errors = PasswordValidator.validate_password(password)
            if not is_valid:
                raise ValidationException("; ".join(errors))
        
        # Hash password
        hashed_password = get_password_hash(password) if password else None
        
        # Generate verification token
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            role=role,
            auth_provider=auth_provider,
            provider_id=provider_id,
            is_verified=is_verified,
            verification_token=verification_token,
            verification_token_expires=verification_expires
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email
        """
        return self.db.query(User).filter(User.email == email).first()
    
    async def get_by_provider(self, provider: AuthProvider, provider_id: str) -> Optional[User]:
        """
        Get user by OAuth provider and provider ID
        """
        return self.db.query(User).filter(
            and_(User.auth_provider == provider, User.provider_id == provider_id)
        ).first()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        """
        user = await self.get_by_email(email)
        if not user:
            return None
        
        if not user.hashed_password:
            return None  # OAuth user, cannot authenticate with password
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        return user
    
    async def update_user(
        self, 
        user_id: int, 
        **updates
    ) -> User:
        """
        Update user information
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", str(user_id))
        
        # Handle password update
        if 'password' in updates:
            password = updates.pop('password')
            is_valid, errors = PasswordValidator.validate_password(password)
            if not is_valid:
                raise ValidationException("; ".join(errors))
            updates['hashed_password'] = get_password_hash(password)
        
        # Update fields
        for field, value in updates.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def change_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", str(user_id))
        
        # Verify current password
        if not user.hashed_password or not verify_password(current_password, user.hashed_password):
            raise AuthenticationException("Current password is incorrect")
        
        # Validate new password
        is_valid, errors = PasswordValidator.validate_password(new_password)
        if not is_valid:
            raise ValidationException("; ".join(errors))
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    async def request_password_reset(self, email: str) -> Optional[str]:
        """
        Request password reset token
        """
        user = await self.get_by_email(email)
        if not user or not user.is_active:
            return None  # Don't reveal if user exists
        
        # Generate reset token
        reset_token = generate_password_reset_token()
        reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        user.reset_token = reset_token
        user.reset_token_expires = reset_expires
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return reset_token
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using token
        """
        user = self.db.query(User).filter(
            and_(
                User.reset_token == token,
                User.reset_token_expires > datetime.utcnow()
            )
        ).first()
        
        if not user:
            raise ValidationException("Invalid or expired reset token")
        
        # Validate new password
        is_valid, errors = PasswordValidator.validate_password(new_password)
        if not is_valid:
            raise ValidationException("; ".join(errors))
        
        # Update password and clear reset token
        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    async def verify_email(self, token: str) -> bool:
        """
        Verify user email using token
        """
        user = self.db.query(User).filter(
            and_(
                User.verification_token == token,
                User.verification_token_expires > datetime.utcnow()
            )
        ).first()
        
        if not user:
            raise ValidationException("Invalid or expired verification token")
        
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    async def resend_verification_email(self, email: str) -> Optional[str]:
        """
        Resend verification email
        """
        user = await self.get_by_email(email)
        if not user or user.is_verified:
            return None
        
        # Generate new verification token
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        user.verification_token = verification_token
        user.verification_token_expires = verification_expires
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return verification_token
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        auth_provider: Optional[AuthProvider] = None
    ) -> tuple[List[User], int]:
        """
        Get users with filtering and pagination
        """
        query = self.db.query(User)
        
        # Apply filters
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                User.company_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if auth_provider:
            query = query.filter(User.auth_provider == auth_provider)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        
        return users, total
    
    async def activate_user(self, user_id: int) -> User:
        """
        Activate user account
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", str(user_id))
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate user account
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", str(user_id))
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user account (soft delete by deactivation)
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User", str(user_id))
        
        # Instead of hard delete, deactivate and anonymize
        user.is_active = False
        user.email = f"deleted_user_{user_id}@example.com"
        user.first_name = "Deleted"
        user.last_name = "User"
        user.company_name = None
        user.phone = None
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics
        """
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        verified_users = self.db.query(User).filter(User.is_verified == True).count()
        
        # Users by role
        role_stats = {}
        for role in UserRole:
            count = self.db.query(User).filter(User.role == role).count()
            role_stats[role.value] = count
        
        # Users by auth provider
        provider_stats = {}
        for provider in AuthProvider:
            count = self.db.query(User).filter(User.auth_provider == provider).count()
            provider_stats[provider.value] = count
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "role_distribution": role_stats,
            "auth_provider_distribution": provider_stats,
        }