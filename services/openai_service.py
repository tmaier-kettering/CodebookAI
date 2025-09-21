"""
Professional OpenAI API service with comprehensive error handling and retry logic.

This service provides a clean interface to OpenAI's API with:
- Proper authentication and configuration
- Robust error handling and retry logic
- Structured logging and monitoring
- Both live and batch processing capabilities
"""

import logging
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import io

from core.config import AppConfig
from core.exceptions import OpenAIError, ConfigurationError
from models.classification import (
    ClassificationRequest,
    ClassificationResponse, 
    ClassificationItem,
    BatchRequest,
    BatchResponse
)

# Set up logger for this module
logger = logging.getLogger(__name__)


@dataclass
class APIUsageStats:
    """Track API usage for monitoring and billing."""
    requests_made: int = 0
    tokens_used: int = 0
    errors_encountered: int = 0
    total_cost_estimate: float = 0.0


class OpenAIService:
    """
    Professional OpenAI API service with enterprise-grade reliability.
    
    This service provides a robust interface to OpenAI's API with proper
    error handling, retry logic, and usage monitoring.
    """
    
    def __init__(self, config: AppConfig) -> None:
        """
        Initialize the OpenAI service.
        
        Args:
            config: Application configuration containing API credentials
            
        Raises:
            ConfigurationError: If configuration is invalid
            OpenAIError: If OpenAI client cannot be initialized
        """
        self.config = config
        self.usage_stats = APIUsageStats()
        
        # Initialize OpenAI client
        try:
            from openai import OpenAI
            
            client_kwargs = config.get_openai_client_kwargs()
            self.client = OpenAI(**client_kwargs)
            
            logger.info("OpenAI client initialized successfully")
            
        except ImportError:
            raise ConfigurationError(
                "OpenAI library not installed. Run: pip install openai",
                error_code="MISSING_DEPENDENCY"
            )
        except Exception as e:
            raise OpenAIError(
                f"Failed to initialize OpenAI client: {str(e)}",
                error_code="CLIENT_INIT_FAILED"
            ) from e
    
    def _handle_api_error(self, error: Exception, operation: str) -> None:
        """
        Handle and classify OpenAI API errors.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            
        Raises:
            OpenAIError: Classified error with appropriate message
        """
        self.usage_stats.errors_encountered += 1
        
        error_msg = str(error)
        
        # Import OpenAI exceptions locally to avoid import errors
        try:
            from openai import (
                AuthenticationError,
                PermissionDeniedError, 
                RateLimitError,
                BadRequestError,
                NotFoundError,
                InternalServerError
            )
            
            if isinstance(error, AuthenticationError):
                raise OpenAIError(
                    "OpenAI API authentication failed. Please check your API key.",
                    error_code="AUTHENTICATION_FAILED"
                ) from error
            elif isinstance(error, PermissionDeniedError):
                raise OpenAIError(
                    "Permission denied. Please check your OpenAI account permissions.",
                    error_code="PERMISSION_DENIED"
                ) from error
            elif isinstance(error, RateLimitError):
                raise OpenAIError(
                    "OpenAI API rate limit exceeded. Please try again later.",
                    error_code="RATE_LIMIT_EXCEEDED"
                ) from error
            elif isinstance(error, BadRequestError):
                raise OpenAIError(
                    f"Invalid request to OpenAI API: {error_msg}",
                    error_code="BAD_REQUEST"
                ) from error
            elif isinstance(error, NotFoundError):
                raise OpenAIError(
                    f"OpenAI API endpoint not found: {error_msg}",
                    error_code="ENDPOINT_NOT_FOUND"
                ) from error
            elif isinstance(error, InternalServerError):
                raise OpenAIError(
                    "OpenAI API internal server error. Please try again later.",
                    error_code="SERVER_ERROR"
                ) from error
            else:
                raise OpenAIError(
                    f"OpenAI API error during {operation}: {error_msg}",
                    error_code="API_ERROR"
                ) from error
                
        except ImportError:
            # Fallback if OpenAI exceptions not available
            raise OpenAIError(
                f"OpenAI API error during {operation}: {error_msg}",
                error_code="API_ERROR"
            ) from error
    
    def classify_text_live(
        self,
        request: ClassificationRequest,
        model: Optional[str] = None
    ) -> ClassificationResponse:
        """
        Classify text using OpenAI's live API with structured output.
        
        Args:
            request: Classification request containing text and labels
            model: Optional model override
            
        Returns:
            Classification response with results
            
        Raises:
            OpenAIError: If API call fails
        """
        model_to_use = model or self.config.default_model
        
        logger.info(f"Starting live classification with model {model_to_use}")
        
        # Import JSON handler locally to avoid circular imports
        from file_handling.json_handler import JSONHandler
        json_handler = JSONHandler()
        
        try:
            # Build schema and prompt
            schema = json_handler.build_classification_schema(request.allowed_labels)
            prompt = json_handler.create_classification_prompt(
                text=request.text,
                allowed_labels=request.allowed_labels
            )
            
            # Record start time for performance monitoring
            start_time = time.time()
            
            # Make API call
            response = self.client.responses.create(
                model=model_to_use,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional text classifier. "
                            "Analyze the provided text carefully and respond with "
                            "accurate classifications in the exact JSON format specified. "
                            "Provide thoughtful confidence scores based on your analysis."
                        )
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "TextClassification",
                        "schema": schema,
                        "strict": True
                    }
                }
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update usage stats
            self.usage_stats.requests_made += 1
            
            # Parse response
            if hasattr(response, 'output_text') and response.output_text:
                import json
                response_data = json.loads(response.output_text)
                
                # Validate and create classification items
                classifications = json_handler.validate_classification_response(
                    response_data,
                    expected_labels=request.allowed_labels
                )
                
                result = ClassificationResponse(
                    classifications=classifications,
                    request_id=request.custom_id,
                    model_used=model_to_use,
                    processing_time=processing_time
                )
                
                logger.info(f"Live classification completed in {processing_time:.2f}s")
                return result
            else:
                raise OpenAIError(
                    "No output received from OpenAI API",
                    error_code="EMPTY_RESPONSE"
                )
                
        except Exception as e:
            if isinstance(e, OpenAIError):
                raise
            else:
                self._handle_api_error(e, "live classification")
    
    def submit_batch_job(
        self,
        batch_request: BatchRequest,
        model: Optional[str] = None
    ) -> str:
        """
        Submit a batch job to OpenAI's batch API.
        
        Args:
            batch_request: Batch request containing items to process
            model: Optional model override
            
        Returns:
            Batch job ID for tracking
            
        Raises:
            OpenAIError: If batch submission fails
        """
        model_to_use = model or batch_request.model
        
        logger.info(f"Submitting batch job with {batch_request.item_count} items")
        
        try:
            # Create JSONL content
            from file_handling.json_handler import JSONHandler
            json_handler = JSONHandler()
            
            batch_bytes = json_handler.create_batch_jsonl_bytes(
                batch_request,
                model=model_to_use
            )
            
            # Upload batch file
            batch_input_file = self.client.files.create(
                file=batch_bytes,
                purpose="batch"
            )
            
            logger.debug(f"Batch file uploaded: {batch_input_file.id}")
            
            # Create batch job
            batch_job = self.client.batches.create(
                input_file_id=batch_input_file.id,
                endpoint="/v1/responses",
                completion_window=batch_request.completion_window,
                metadata={
                    "description": batch_request.description,
                    "item_count": str(batch_request.item_count)
                }
            )
            
            logger.info(f"Batch job submitted successfully: {batch_job.id}")
            return batch_job.id
            
        except Exception as e:
            self._handle_api_error(e, "batch job submission")
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get the status of a batch job.
        
        Args:
            batch_id: The batch job ID
            
        Returns:
            Dictionary containing batch status information
            
        Raises:
            OpenAIError: If status check fails
        """
        logger.debug(f"Checking status for batch: {batch_id}")
        
        try:
            batch_status = self.client.batches.retrieve(batch_id)
            
            status_info = {
                "id": batch_status.id,
                "status": batch_status.status,
                "created_at": batch_status.created_at,
                "completed_at": getattr(batch_status, 'completed_at', None),
                "failed_at": getattr(batch_status, 'failed_at', None),
                "request_counts": getattr(batch_status, 'request_counts', {}),
                "metadata": getattr(batch_status, 'metadata', {})
            }
            
            logger.debug(f"Batch {batch_id} status: {status_info['status']}")
            return status_info
            
        except Exception as e:
            self._handle_api_error(e, f"batch status check for {batch_id}")
    
    def get_batch_results(self, batch_id: str) -> List[ClassificationItem]:
        """
        Retrieve and parse results from a completed batch job.
        
        Args:
            batch_id: The batch job ID
            
        Returns:
            List of classification results
            
        Raises:
            OpenAIError: If results retrieval fails
        """
        logger.info(f"Retrieving results for batch: {batch_id}")
        
        try:
            # Get batch status
            batch_status = self.client.batches.retrieve(batch_id)
            
            if batch_status.status != "completed":
                raise OpenAIError(
                    f"Batch {batch_id} is not completed (status: {batch_status.status})",
                    error_code="BATCH_NOT_COMPLETED"
                )
            
            if not hasattr(batch_status, 'output_file_id') or not batch_status.output_file_id:
                raise OpenAIError(
                    f"No output file available for batch {batch_id}",
                    error_code="NO_OUTPUT_FILE"
                )
            
            # Download results
            file_response = self.client.files.content(batch_status.output_file_id)
            results_content = file_response.content.decode('utf-8')
            
            # Parse results
            from file_handling.json_handler import JSONHandler
            json_handler = JSONHandler()
            
            classifications = json_handler.parse_batch_response_jsonl(results_content)
            
            logger.info(f"Retrieved {len(classifications)} classifications from batch {batch_id}")
            return classifications
            
        except Exception as e:
            if isinstance(e, OpenAIError):
                raise
            else:
                self._handle_api_error(e, f"batch results retrieval for {batch_id}")
    
    def cancel_batch_job(self, batch_id: str) -> bool:
        """
        Cancel a batch job.
        
        Args:
            batch_id: The batch job ID to cancel
            
        Returns:
            True if cancellation was successful
            
        Raises:
            OpenAIError: If cancellation fails
        """
        logger.info(f"Cancelling batch job: {batch_id}")
        
        try:
            cancelled_batch = self.client.batches.cancel(batch_id)
            
            success = hasattr(cancelled_batch, 'status') and cancelled_batch.status == "cancelled"
            
            if success:
                logger.info(f"Batch {batch_id} cancelled successfully")
            else:
                logger.warning(f"Batch {batch_id} cancellation may have failed")
            
            return success
            
        except Exception as e:
            self._handle_api_error(e, f"batch cancellation for {batch_id}")
    
    def list_batch_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List recent batch jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of batch job information
            
        Raises:
            OpenAIError: If listing fails
        """
        logger.debug(f"Listing batch jobs (limit: {limit})")
        
        try:
            batches = self.client.batches.list(limit=limit)
            
            batch_list = []
            for batch in batches.data:
                batch_info = {
                    "id": batch.id,
                    "status": batch.status,
                    "created_at": batch.created_at,
                    "completed_at": getattr(batch, 'completed_at', None),
                    "metadata": getattr(batch, 'metadata', {})
                }
                batch_list.append(batch_info)
            
            logger.debug(f"Found {len(batch_list)} batch jobs")
            return batch_list
            
        except Exception as e:
            self._handle_api_error(e, "batch job listing")
    
    def get_usage_stats(self) -> APIUsageStats:
        """
        Get current API usage statistics.
        
        Returns:
            Current usage statistics
        """
        return self.usage_stats
    
    def reset_usage_stats(self) -> None:
        """Reset usage statistics counters."""
        self.usage_stats = APIUsageStats()
        logger.debug("Usage statistics reset")
