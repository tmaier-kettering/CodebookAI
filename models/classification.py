"""
Data models for text classification operations.

This module defines strongly-typed data classes that represent the various
entities used in the text classification workflow. These models provide:
- Type safety and validation
- Clear data contracts between components
- Serialization/deserialization capabilities
- Documentation of data structures
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
import json
from pathlib import Path


@dataclass(frozen=True)
class ClassificationItem:
    """
    Represents a single text classification result.
    
    This is the fundamental unit of classification data, containing the original
    text, assigned label, and confidence score.
    
    Attributes:
        quote: The original text that was classified
        label: The assigned classification label
        confidence: Confidence score between 0.0 and 1.0
    """
    quote: str
    label: str
    confidence: float
    
    def __post_init__(self) -> None:
        """Validate the classification item after creation."""
        if not self.quote.strip():
            raise ValueError("Quote cannot be empty or whitespace only")
        
        if not self.label.strip():
            raise ValueError("Label cannot be empty or whitespace only")
            
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
    
    def to_dict(self) -> Dict[str, Union[str, float]]:
        """Convert to dictionary for serialization."""
        return {
            'quote': self.quote,
            'label': self.label,
            'confidence': self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClassificationItem':
        """Create instance from dictionary."""
        return cls(
            quote=str(data['quote']),
            label=str(data['label']),
            confidence=float(data['confidence'])
        )


@dataclass(frozen=True)
class ClassificationRequest:
    """
    Represents a request to classify a single text.
    
    This encapsulates all the information needed to perform a classification,
    including the text to classify and the allowed labels.
    
    Attributes:
        text: The text to be classified
        allowed_labels: List of valid labels for classification
        custom_id: Optional identifier for tracking this request
    """
    text: str
    allowed_labels: List[str]
    custom_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate the classification request after creation."""
        if not self.text.strip():
            raise ValueError("Text cannot be empty or whitespace only")
            
        if not self.allowed_labels:
            raise ValueError("At least one allowed label must be provided")
            
        if len(set(self.allowed_labels)) != len(self.allowed_labels):
            raise ValueError("Allowed labels must be unique")
            
        for label in self.allowed_labels:
            if not str(label).strip():
                raise ValueError("All labels must be non-empty strings")


@dataclass(frozen=True)
class ClassificationResponse:
    """
    Represents the response from a classification operation.
    
    This contains the classification results along with metadata about
    the classification process.
    
    Attributes:
        classifications: List of classification results
        request_id: Optional identifier linking back to the request
        model_used: The model that performed the classification
        processing_time: Optional processing time in seconds
    """
    classifications: List[ClassificationItem]
    request_id: Optional[str] = None
    model_used: Optional[str] = None
    processing_time: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Validate the classification response after creation."""
        if not self.classifications:
            raise ValueError("At least one classification result must be provided")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'classifications': [item.to_dict() for item in self.classifications],
            'request_id': self.request_id,
            'model_used': self.model_used,
            'processing_time': self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClassificationResponse':
        """Create instance from dictionary."""
        classifications = [
            ClassificationItem.from_dict(item_data) 
            for item_data in data['classifications']
        ]
        
        return cls(
            classifications=classifications,
            request_id=data.get('request_id'),
            model_used=data.get('model_used'),
            processing_time=data.get('processing_time')
        )


@dataclass(frozen=True)
class BatchItem:
    """
    Represents a single item in a batch processing request.
    
    This combines the classification request with batch-specific metadata
    like custom IDs for tracking individual items in the batch.
    
    Attributes:
        request: The classification request
        custom_id: Unique identifier for this item within the batch
    """
    request: ClassificationRequest
    custom_id: str
    
    def __post_init__(self) -> None:
        """Validate the batch item after creation."""
        if not self.custom_id.strip():
            raise ValueError("Custom ID cannot be empty or whitespace only")


@dataclass(frozen=True)
class BatchRequest:
    """
    Represents a batch processing request containing multiple classification items.
    
    This encapsulates all the information needed to submit a batch job to
    the OpenAI API, including metadata and processing options.
    
    Attributes:
        items: List of batch items to process
        model: The OpenAI model to use for classification
        completion_window: How long to allow for batch completion
        description: Human-readable description of the batch
        metadata: Additional metadata for the batch
    """
    items: List[BatchItem]
    model: str = "gpt-4-turbo-preview"
    completion_window: str = "24h"
    description: str = "text_classification"
    metadata: Optional[Dict[str, str]] = None
    
    def __post_init__(self) -> None:
        """Validate the batch request after creation."""
        if not self.items:
            raise ValueError("At least one batch item must be provided")
            
        # Validate that all custom IDs are unique
        custom_ids = [item.custom_id for item in self.items]
        if len(set(custom_ids)) != len(custom_ids):
            raise ValueError("All custom IDs in batch must be unique")
    
    @property
    def item_count(self) -> int:
        """Get the number of items in this batch."""
        return len(self.items)
    
    def get_all_labels(self) -> List[str]:
        """Get all unique labels used across all items in the batch."""
        all_labels = set()
        for item in self.items:
            all_labels.update(item.request.allowed_labels)
        return sorted(list(all_labels))


@dataclass(frozen=True)
class BatchResponse:
    """
    Represents the response from a batch processing operation.
    
    This contains all the classification results from the batch along with
    metadata about the batch processing.
    
    Attributes:
        responses: List of classification responses
        batch_id: OpenAI batch job identifier
        status: Current status of the batch job
        created_at: When the batch was created
        completed_at: When the batch completed (if finished)
        failed_count: Number of items that failed processing
        succeeded_count: Number of items that succeeded
    """
    responses: List[ClassificationResponse]
    batch_id: str
    status: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_count: int = 0
    succeeded_count: int = 0
    
    def __post_init__(self) -> None:
        """Validate the batch response after creation."""
        if not self.batch_id.strip():
            raise ValueError("Batch ID cannot be empty")
            
        if self.failed_count < 0 or self.succeeded_count < 0:
            raise ValueError("Failed and succeeded counts must be non-negative")
    
    @property
    def total_items(self) -> int:
        """Get the total number of items processed."""
        return self.failed_count + self.succeeded_count
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the batch (0.0 to 1.0)."""
        total = self.total_items
        return self.succeeded_count / total if total > 0 else 0.0
    
    def get_all_classifications(self) -> List[ClassificationItem]:
        """Get all classification items from all responses."""
        all_items = []
        for response in self.responses:
            all_items.extend(response.classifications)
        return all_items
