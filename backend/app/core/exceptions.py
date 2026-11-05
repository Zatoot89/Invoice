"""
InvoiceFlow Pro - Custom Exceptions
"""
from typing import Any, Dict, Optional


class InvoiceFlowException(Exception):
    """Base exception class for InvoiceFlow Pro"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


# Authentication Exceptions
class AuthenticationException(InvoiceFlowException):
    """Authentication related exceptions"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR",
            details=details,
        )


class AuthorizationException(InvoiceFlowException):
    """Authorization related exceptions"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


class InvalidTokenException(InvoiceFlowException):
    """Invalid token exceptions"""
    
    def __init__(self, message: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="INVALID_TOKEN",
            details=details,
        )


class TokenExpiredException(InvoiceFlowException):
    """Token expired exceptions"""
    
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="TOKEN_EXPIRED",
            details=details,
        )


# Resource Exceptions
class ResourceNotFoundException(InvoiceFlowException):
    """Resource not found exceptions"""
    
    def __init__(self, resource: str, identifier: str = "", details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
        )


class ResourceAlreadyExistsException(InvoiceFlowException):
    """Resource already exists exceptions"""
    
    def __init__(self, resource: str, identifier: str = "", details: Optional[Dict[str, Any]] = None):
        message = f"{resource} already exists"
        if identifier:
            message += f" with identifier: {identifier}"
        super().__init__(
            message=message,
            status_code=409,
            error_code="RESOURCE_ALREADY_EXISTS",
            details=details,
        )


# Validation Exceptions
class ValidationException(InvoiceFlowException):
    """Validation related exceptions"""
    
    def __init__(self, message: str, field: str = "", details: Optional[Dict[str, Any]] = None):
        if field:
            message = f"Validation error for field '{field}': {message}"
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


# Business Logic Exceptions
class InvoiceException(InvoiceFlowException):
    """Invoice related exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVOICE_ERROR",
            details=details,
        )


class PaymentException(InvoiceFlowException):
    """Payment related exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="PAYMENT_ERROR",
            details=details,
        )


class CurrencyException(InvoiceFlowException):
    """Currency related exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="CURRENCY_ERROR",
            details=details,
        )


# External Service Exceptions
class ExternalServiceException(InvoiceFlowException):
    """External service exceptions"""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"External service error ({service}): {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )


class RateLimitException(InvoiceFlowException):
    """Rate limit exceeded exceptions"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


# File Upload Exceptions
class FileUploadException(InvoiceFlowException):
    """File upload exceptions"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="FILE_UPLOAD_ERROR",
            details=details,
        )


class FileSizeException(InvoiceFlowException):
    """File size exceeded exceptions"""
    
    def __init__(self, max_size: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"File size exceeds maximum allowed size of {max_size}MB",
            status_code=413,
            error_code="FILE_SIZE_EXCEEDED",
            details=details,
        )