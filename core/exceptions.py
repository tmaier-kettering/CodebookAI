"""
Custom exception hierarchy for better error handling and debugging.

This module defines a hierarchy of exceptions that provide clear, actionable
error messages and help developers quickly identify and fix issues.
"""

from typing import Optional, Any


class CodebookError(Exception):
    """
    Base exception for all Codebook-related errors.
    
    This is the root exception that all other custom exceptions inherit from.
    It provides a consistent interface for error handling throughout the application.
    
    Attributes:
        message: Human-readable error description
        error_code: Optional error code for programmatic handling
        context: Optional dictionary containing additional error context
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Initialize the base exception.
        
        Args:
            message: Clear, actionable error message
            error_code: Optional code for programmatic error handling
            context: Additional context information for debugging
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        """Return a formatted error message."""
        base_msg = self.message
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        return base_msg


class ConfigurationError(CodebookError):
    """
    Raised when there are issues with application configuration.
    
    This includes missing environment variables, invalid configuration values,
    or problems loading configuration files.
    """
    pass


class ValidationError(CodebookError):
    """
    Raised when input validation fails.
    
    This includes invalid file formats, empty data, or data that doesn't
    meet the expected schema requirements.
    """
    pass


class OpenAIError(CodebookError):
    """
    Raised when there are issues with OpenAI API interactions.
    
    This includes authentication failures, API rate limits, invalid responses,
    or network connectivity issues.
    """
    pass


class FileProcessingError(CodebookError):
    """
    Raised when there are issues processing files.
    
    This includes file I/O errors, parsing failures, or unsupported file formats.
    """
    pass
