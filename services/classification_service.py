"""
High-level classification service that orchestrates the complete workflow.

This service provides the main business logic for text classification,
coordinating between file handling, API calls, and result processing.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import time

from core.config import AppConfig
from core.exceptions import ValidationError, CodebookError
from models.classification import (
    ClassificationRequest,
    ClassificationResponse,
    ClassificationItem,
    BatchItem,
    BatchRequest,
    BatchResponse
)
from services.openai_service import OpenAIService
from file_handling.csv_handler import CSVHandler
from file_handling.json_handler import JSONHandler

# Set up logger for this module
logger = logging.getLogger(__name__)


class ClassificationService:
    """
    High-level service for text classification operations.
    
    This service orchestrates the complete classification workflow from
    data input through API processing to result output.
    """
    
    def __init__(self, config: AppConfig) -> None:
        """
        Initialize the classification service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.openai_service = OpenAIService(config)
        self.csv_handler = CSVHandler()
        self.json_handler = JSONHandler()
        
        logger.info("ClassificationService initialized")
    
    def load_labels_from_file(
        self, 
        file_path: Optional[Path] = None,
        has_headers: bool = False
    ) -> List[str]:
        """
        Load classification labels from a CSV file.
        
        Args:
            file_path: Path to labels file (if None, will prompt with GUI)
            has_headers: Whether the CSV has headers
            
        Returns:
            List of unique labels
            
        Raises:
            ValidationError: If no valid labels found
            CodebookError: If file loading fails
        """
        logger.info("Loading classification labels")
        
        if file_path is None:
            # Use GUI to select file
            labels, selected_path = self.csv_handler.import_csv_with_gui(
                title="Select Labels CSV File",
                filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
            )
            
            if labels is None:
                raise ValidationError(
                    "No labels file selected",
                    error_code="NO_FILE_SELECTED"
                )
            
            logger.info(f"Loaded {len(labels)} labels from GUI selection")
            return labels
        else:
            # Load from specified path
            labels = self.csv_handler.read_labels_from_csv(
                file_path=file_path,
                has_headers=has_headers,
                column_index=0
            )
            
            logger.info(f"Loaded {len(labels)} labels from {file_path}")
            return labels
    
    def load_texts_from_file(
        self,
        file_path: Optional[Path] = None,
        has_headers: bool = False,
        text_column: int = 0
    ) -> List[str]:
        """
        Load texts to classify from a CSV file.
        
        Args:
            file_path: Path to texts file (if None, will prompt with GUI)
            has_headers: Whether the CSV has headers
            text_column: Which column contains the text
            
        Returns:
            List of texts to classify
            
        Raises:
            ValidationError: If no valid texts found
            CodebookError: If file loading fails
        """
        logger.info("Loading texts for classification")
        
        if file_path is None:
            # Use GUI to select file - we need to modify csv_handler for this
            # For now, let's implement a simpler version
            raise NotImplementedError(
                "GUI text file selection not yet implemented. "
                "Please provide file_path parameter."
            )
        else:
            # Load from specified path
            texts = self.csv_handler.read_texts_from_csv(
                file_path=file_path,
                has_headers=has_headers,
                text_column=text_column
            )
            
            logger.info(f"Loaded {len(texts)} texts from {file_path}")
            return texts
    
    def classify_single_text(
        self,
        text: str,
        allowed_labels: List[str],
        model: Optional[str] = None,
        custom_id: Optional[str] = None
    ) -> ClassificationResponse:
        """
        Classify a single text using live API.
        
        Args:
            text: Text to classify
            allowed_labels: Valid classification labels
            model: Optional model override
            custom_id: Optional custom identifier
            
        Returns:
            Classification response
            
        Raises:
            ValidationError: If inputs are invalid
            CodebookError: If classification fails
        """
        logger.info("Classifying single text")
        
        # Create classification request
        request = ClassificationRequest(
            text=text,
            allowed_labels=allowed_labels,
            custom_id=custom_id
        )
        
        # Perform classification
        response = self.openai_service.classify_text_live(request, model)
        
        logger.info(f"Single text classified successfully")
        return response
    
    def classify_texts_live(
        self,
        texts: List[str],
        allowed_labels: List[str],
        model: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> List[ClassificationResponse]:
        """
        Classify multiple texts using live API calls.
        
        Args:
            texts: List of texts to classify
            allowed_labels: Valid classification labels
            model: Optional model override
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of classification responses
            
        Raises:
            ValidationError: If inputs are invalid
            CodebookError: If classification fails
        """
        logger.info(f"Starting live classification of {len(texts)} texts")
        
        if not texts:
            raise ValidationError(
                "No texts provided for classification",
                error_code="NO_TEXTS"
            )
        
        responses = []
        total_texts = len(texts)
        
        for i, text in enumerate(texts, 1):
            try:
                logger.debug(f"Classifying text {i}/{total_texts}")
                
                # Create request
                request = ClassificationRequest(
                    text=text,
                    allowed_labels=allowed_labels,
                    custom_id=f"live-{i:05d}"
                )
                
                # Classify
                response = self.openai_service.classify_text_live(request, model)
                responses.append(response)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i, total_texts, text[:50] + "..." if len(text) > 50 else text)
                
                # Brief pause to avoid overwhelming the API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to classify text {i}: {str(e)}")
                # Depending on requirements, we might want to continue or stop here
                raise CodebookError(
                    f"Classification failed for text {i}: {str(e)}",
                    error_code="CLASSIFICATION_FAILED",
                    context={"text_index": i, "text_preview": text[:100]}
                ) from e
        
        logger.info(f"Completed live classification of {len(responses)} texts")
        return responses
    
    def submit_batch_classification(
        self,
        texts: List[str],
        allowed_labels: List[str],
        model: Optional[str] = None,
        completion_window: str = "24h",
        description: str = "text_classification"
    ) -> str:
        """
        Submit texts for batch classification.
        
        Args:
            texts: List of texts to classify
            allowed_labels: Valid classification labels
            model: Optional model override
            completion_window: How long to wait for completion
            description: Description for the batch job
            
        Returns:
            Batch job ID for tracking
            
        Raises:
            ValidationError: If inputs are invalid
            CodebookError: If batch submission fails
        """
        logger.info(f"Submitting batch classification for {len(texts)} texts")
        
        if not texts:
            raise ValidationError(
                "No texts provided for batch classification",
                error_code="NO_TEXTS"
            )
        
        # Create batch items
        batch_items = []
        for i, text in enumerate(texts, 1):
            request = ClassificationRequest(
                text=text,
                allowed_labels=allowed_labels,
                custom_id=f"batch-{i:05d}"
            )
            
            batch_item = BatchItem(
                request=request,
                custom_id=f"batch-{i:05d}"
            )
            batch_items.append(batch_item)
        
        # Create batch request
        batch_request = BatchRequest(
            items=batch_items,
            model=model or self.config.default_model,
            completion_window=completion_window,
            description=description
        )
        
        # Submit batch
        batch_id = self.openai_service.submit_batch_job(batch_request, model)
        
        logger.info(f"Batch classification submitted: {batch_id}")
        return batch_id
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get the status of a batch classification job.
        
        Args:
            batch_id: The batch job ID
            
        Returns:
            Status information dictionary
        """
        return self.openai_service.get_batch_status(batch_id)
    
    def retrieve_batch_results(self, batch_id: str) -> List[ClassificationItem]:
        """
        Retrieve results from a completed batch job.
        
        Args:
            batch_id: The batch job ID
            
        Returns:
            List of classification results
        """
        return self.openai_service.get_batch_results(batch_id)
    
    def save_classifications_to_file(
        self,
        classifications: List[ClassificationItem],
        output_path: Optional[Path] = None,
        use_gui: bool = True
    ) -> Optional[Path]:
        """
        Save classification results to a CSV file.
        
        Args:
            classifications: Classification results to save
            output_path: Path to save file (if None and use_gui=True, will prompt)
            use_gui: Whether to use GUI for file selection
            
        Returns:
            Path to saved file or None if cancelled
            
        Raises:
            ValidationError: If no classifications provided
            CodebookError: If save operation fails
        """
        logger.info(f"Saving {len(classifications)} classifications")
        
        if output_path is None and use_gui:
            # Use GUI to select save location
            saved_path = self.csv_handler.save_csv_with_gui(
                classifications=classifications,
                default_filename="classifications.csv"
            )
            
            if saved_path:
                logger.info(f"Classifications saved to: {saved_path}")
            else:
                logger.info("Save operation cancelled by user")
            
            return saved_path
        
        elif output_path is not None:
            # Save to specified path
            self.csv_handler.write_classifications_to_csv(
                classifications=classifications,
                file_path=output_path,
                include_headers=True
            )
            
            logger.info(f"Classifications saved to: {output_path}")
            return output_path
        
        else:
            raise ValidationError(
                "Either output_path must be provided or use_gui must be True",
                error_code="NO_OUTPUT_SPECIFIED"
            )
    
    def process_batch_results_from_bytes(
        self,
        result_bytes: bytes,
        output_path: Optional[Path] = None,
        use_gui: bool = True
    ) -> Optional[Path]:
        """
        Process batch results from raw bytes and save to CSV.
        
        Args:
            result_bytes: Raw JSONL bytes from OpenAI batch API
            output_path: Optional output file path
            use_gui: Whether to use GUI for file selection
            
        Returns:
            Path to saved file or None if cancelled
        """
        logger.info("Processing batch results from bytes")
        
        # Parse classifications from bytes
        classifications = self.csv_handler.parse_batch_results_from_jsonl_bytes(result_bytes)
        
        # Save to file
        return self.save_classifications_to_file(
            classifications=classifications,
            output_path=output_path,
            use_gui=use_gui
        )
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        Get current API usage statistics.
        
        Returns:
            Dictionary containing usage statistics
        """
        stats = self.openai_service.get_usage_stats()
        return {
            "requests_made": stats.requests_made,
            "tokens_used": stats.tokens_used,
            "errors_encountered": stats.errors_encountered,
            "estimated_cost": stats.total_cost_estimate
        }
    
    def cancel_batch_job(self, batch_id: str) -> bool:
        """
        Cancel a batch classification job.
        
        Args:
            batch_id: The batch job ID to cancel
            
        Returns:
            True if cancellation was successful
        """
        return self.openai_service.cancel_batch_job(batch_id)
    
    def list_batch_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List recent batch classification jobs.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of batch job information
        """
        return self.openai_service.list_batch_jobs(limit)
