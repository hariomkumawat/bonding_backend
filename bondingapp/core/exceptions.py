"""
Custom exception handler for consistent API error responses
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    Throttled,
)
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses
    
    Format:
    {
        "error": {
            "code": "error_code",
            "message": "Human readable message",
            "details": {...}  # Optional additional details
        }
    }
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, it's not a DRF exception
    if response is None:
        # Handle Django's Http404
        if isinstance(exc, Http404):
            return Response(
                {
                    "error": {
                        "code": "not_found",
                        "message": "The requested resource was not found.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Handle Django's ValidationError
        if isinstance(exc, DjangoValidationError):
            return Response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "Validation failed.",
                        "details": exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log unexpected errors
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        # Return generic 500 error for unexpected exceptions
        return Response(
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred. Please try again later.",
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Customize DRF exception responses
    error_data = {
        "error": {
            "code": get_error_code(exc),
            "message": get_error_message(exc),
        }
    }
    
    # Add details if available
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            error_data["error"]["details"] = exc.detail
        elif isinstance(exc.detail, list):
            error_data["error"]["details"] = exc.detail
        else:
            error_data["error"]["message"] = str(exc.detail)
    
    # Add throttle information
    if isinstance(exc, Throttled):
        error_data["error"]["retry_after_seconds"] = exc.wait
    
    response.data = error_data
    
    return response


def get_error_code(exc):
    """Get error code based on exception type"""
    
    error_codes = {
        ValidationError: "validation_error",
        AuthenticationFailed: "authentication_failed",
        NotAuthenticated: "not_authenticated",
        PermissionDenied: "permission_denied",
        NotFound: "not_found",
        MethodNotAllowed: "method_not_allowed",
        Throttled: "rate_limit_exceeded",
    }
    
    for exception_class, code in error_codes.items():
        if isinstance(exc, exception_class):
            return code
    
    return "error"


def get_error_message(exc):
    """Get user-friendly error message"""
    
    error_messages = {
        ValidationError: "The provided data is invalid.",
        AuthenticationFailed: "Authentication failed. Please check your credentials.",
        NotAuthenticated: "Authentication required. Please log in.",
        PermissionDenied: "You don't have permission to perform this action.",
        NotFound: "The requested resource was not found.",
        MethodNotAllowed: "This HTTP method is not allowed for this endpoint.",
        Throttled: "Too many requests. Please slow down.",
    }
    
    for exception_class, message in error_messages.items():
        if isinstance(exc, exception_class):
            return message
    
    return "An error occurred."


# Custom exception classes
class PartnerAlreadyLinkedError(ValidationError):
    """Raised when user already has a partner"""
    default_detail = "You already have a partner linked to your account."
    default_code = "partner_already_linked"


class PartnerNotFoundError(NotFound):
    """Raised when partner is not found"""
    default_detail = "Partner not found."
    default_code = "partner_not_found"


class InsufficientCoinsError(ValidationError):
    """Raised when user doesn't have enough coins"""
    default_detail = "You don't have enough coins for this action."
    default_code = "insufficient_coins"


class SkipLimitExceededError(ValidationError):
    """Raised when user exceeds daily skip limit"""
    default_detail = "You have reached your daily skip limit."
    default_code = "skip_limit_exceeded"


class ActivityAlreadyCompletedError(ValidationError):
    """Raised when activity is already completed"""
    default_detail = "You have already completed this activity today."
    default_code = "activity_already_completed"


class InvalidInvitationCodeError(ValidationError):
    """Raised when invitation code is invalid"""
    default_detail = "Invalid invitation code."
    default_code = "invalid_invitation_code"


class CannotLinkToSelfError(ValidationError):
    """Raised when user tries to link to themselves"""
    default_detail = "You cannot link to your own account."
    default_code = "cannot_link_to_self"