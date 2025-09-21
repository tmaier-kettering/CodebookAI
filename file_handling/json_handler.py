"""
Professional JSON and JSONL handling for OpenAI API integration.

This module provides robust JSON/JSONL operations for:
- Building OpenAI API schemas and requests  
- Processing batch API responses
- Validating data structures
- Managing API payloads with proper error handling
"""

import json
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from dataclasses import asdict

from core.exceptions import ValidationError, FileProcessingError
from models.classification import (
    ClassificationRequest, 
    BatchItem, 
    BatchRequest,
    ClassificationItem
)

# Set up logger for this module
logger = logging.getLogger(__name__)


class JSONHandler:
    """
    Professional JSON/JSONL handler for OpenAI API operations.
    
    This class provides methods for creating OpenAI API requests, processing
    responses, and managing JSON schemas with comprehensive error handling.
    """
    
    def __init__(self) -> None:
        """Initialize the JSON handler."""
        logger.debug("JSONHandler initialized")
    
    def build_classification_schema(self, allowed_labels: List[str]) -> Dict[str, Any]:
        """
        Build JSON schema for text classification responses.
        
        This creates a strict JSON schema that OpenAI's structured output
        feature will use to ensure responses match the expected format.
        
        Args:
            allowed_labels: List of valid classification labels
            
        Returns:
            JSON schema dictionary for OpenAI structured output
            
        Raises:
            ValidationError: If labels are invalid
        """
        if not allowed_labels:
            raise ValidationError(
                "At least one label must be provided for schema",
                error_code="NO_LABELS_PROVIDED"
            )
        
        # Validate and normalize labels
        normalized_labels = []
        for label in allowed_labels:
            label_str = str(label).strip()
            if not label_str:
                raise ValidationError(
                    "All labels must be non-empty strings",
                    error_code="EMPTY_LABEL"
                )
            normalized_labels.append(label_str)
        
        # Remove duplicates while preserving order
        unique_labels = []
        seen = set()
        for label in normalized_labels:
            if label not in seen:
                unique_labels.append(label)
                seen.add(label)
        
        logger.debug(f"Building schema for {len(unique_labels)} labels: {unique_labels}")
        
        # Define the schema for a single classification item
        item_schema = {
            "type": "object",
            "properties": {
                "quote": {
                    "type": "string",
                    "minLength": 1,
                    "description": "The original text that was classified"
                },
                "label": {
                    "type": "string",
                    "enum": unique_labels,
                    "description": f"The assigned label, must be one of: {', '.join(unique_labels)}"
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence score between 0.0 and 1.0"
                }
            },
            "required": ["quote", "label", "confidence"],
            "additionalProperties": False
        }
        
        # Build the complete response schema
        schema = {
            "type": "object",
            "properties": {
                "classifications": {
                    "type": "array",
                    "items": item_schema,
                    "minItems": 1,
                    "description": "Array of classification results"
                }
            },
            "required": ["classifications"],
            "additionalProperties": False
        }
        
        logger.debug("Classification schema built successfully")
        return schema
    
    def create_classification_prompt(
        self, 
        text: str, 
        allowed_labels: List[str]
    ) -> str:
        """
        Create a clear, professional prompt for text classification.
        
        Args:
            text: Text to be classified
            allowed_labels: List of valid labels
            
        Returns:
            Formatted prompt string
            
        Raises:
            ValidationError: If inputs are invalid
        """
        if not text.strip():
            raise ValidationError(
                "Text to classify cannot be empty",
                error_code="EMPTY_TEXT"
            )
        
        if not allowed_labels:
            raise ValidationError(
                "At least one label must be provided",
                error_code="NO_LABELS_PROVIDED"
            )
        
        # Create a clear, professional prompt
        prompt = (
            "Classify the following text into exactly one of the allowed labels. "
            "Return your response as JSON only, following the provided schema.\n\n"
            f"Allowed labels: {', '.join(allowed_labels)}\n\n"
            f"Text to classify: \"{text}\"\n\n"
            "Instructions:\n"
            "1. Read the text carefully\n"
            "2. Choose the most appropriate label from the allowed list\n"
            "3. Provide a confidence score between 0.0 and 1.0\n"
            "4. Return only valid JSON matching the schema"
        )
        
        return prompt
    
    def create_batch_jsonl_content(
        self,
        batch_request: BatchRequest,
        model: Optional[str] = None
    ) -> str:
        """
        Create JSONL content for OpenAI batch API.
        
        Args:
            batch_request: Batch request containing items to process
            model: Optional model override
            
        Returns:
            JSONL formatted string for batch processing
            
        Raises:
            ValidationError: If batch request is invalid
        """
        if not batch_request.items:
            raise ValidationError(
                "Batch request must contain at least one item",
                error_code="EMPTY_BATCH"
            )
        
        # Use model from request or override
        model_to_use = model or batch_request.model
        
        logger.info(f"Creating JSONL for {len(batch_request.items)} items using model {model_to_use}")
        
        # Get all unique labels for schema
        all_labels = batch_request.get_all_labels()
        schema = self.build_classification_schema(all_labels)
        
        jsonl_lines = []
        
        for item in batch_request.items:
            # Create the prompt
            prompt = self.create_classification_prompt(
                item.request.text,
                item.request.allowed_labels
            )
            
            # Build the API request
            api_request = {
                "custom_id": item.custom_id,
                "method": "POST",
                "url": "/v1/responses",
                "body": {
                    "model": model_to_use,
                    "input": [
                        {
                            "role": "system",
                            "content": (
                                "You are a professional text classifier. "
                                "Analyze the provided text and respond with accurate "
                                "classifications in the exact JSON format specified. "
                                "Always provide thoughtful confidence scores."
                            )
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "text": {
                        "format": {
                            "type": "json_schema",
                            "name": "TextClassification",
                            "schema": schema,
                            "strict": True
                        }
                    }
                }
            }
            
            # Convert to JSON and add to lines
            try:
                json_line = json.dumps(api_request, ensure_ascii=False)
                jsonl_lines.append(json_line)
            except (TypeError, ValueError) as e:
                raise ValidationError(
                    f"Failed to serialize request for item {item.custom_id}: {str(e)}",
                    error_code="SERIALIZATION_ERROR"
                ) from e
        
        # Join all lines with newlines
        jsonl_content = "\n".join(jsonl_lines)
        
        logger.debug(f"Generated JSONL with {len(jsonl_lines)} requests")
        return jsonl_content
    
    def create_batch_jsonl_bytes(
        self,
        batch_request: BatchRequest,
        model: Optional[str] = None
    ) -> io.BytesIO:
        """
        Create JSONL content as bytes for direct upload to OpenAI.
        
        Args:
            batch_request: Batch request containing items to process
            model: Optional model override
            
        Returns:
            BytesIO object containing JSONL data
            
        Raises:
            ValidationError: If batch request is invalid
        """
        # Generate JSONL content
        jsonl_content = self.create_batch_jsonl_content(batch_request, model)
        
        # Create BytesIO buffer
        buffer = io.BytesIO()
        buffer.write(jsonl_content.encode('utf-8'))
        buffer.seek(0)
        
        # Set filename for OpenAI API
        buffer.name = f"batch_{batch_request.description}.jsonl"
        
        logger.debug(f"Created JSONL bytes buffer: {len(jsonl_content)} characters")
        return buffer
    
    def write_batch_jsonl_file(
        self,
        batch_request: BatchRequest,
        output_path: Path,
        model: Optional[str] = None
    ) -> Path:
        """
        Write batch JSONL to file.
        
        Args:
            batch_request: Batch request containing items to process
            output_path: Path where to write the JSONL file
            model: Optional model override
            
        Returns:
            Path to the created file
            
        Raises:
            FileProcessingError: If file cannot be written
            ValidationError: If batch request is invalid
        """
        logger.info(f"Writing batch JSONL to: {output_path}")
        
        # Generate JSONL content
        jsonl_content = self.create_batch_jsonl_content(batch_request, model)
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(jsonl_content)
            
            logger.info(f"Successfully wrote JSONL file: {output_path}")
            return output_path.resolve()
            
        except Exception as e:
            raise FileProcessingError(
                f"Failed to write JSONL file {output_path}: {str(e)}",
                error_code="FILE_WRITE_ERROR"
            ) from e
    
    def validate_classification_response(
        self, 
        response_data: Dict[str, Any],
        expected_labels: Optional[List[str]] = None
    ) -> List[ClassificationItem]:
        """
        Validate and parse classification response from OpenAI.
        
        Args:
            response_data: Raw response data from OpenAI
            expected_labels: Optional list of expected labels for validation
            
        Returns:
            List of validated classification items
            
        Raises:
            ValidationError: If response format is invalid
        """
        logger.debug("Validating classification response")
        
        if not isinstance(response_data, dict):
            raise ValidationError(
                "Response must be a dictionary",
                error_code="INVALID_RESPONSE_TYPE"
            )
        
        # Check for classifications array
        classifications_data = response_data.get('classifications')
        if not isinstance(classifications_data, list):
            raise ValidationError(
                "Response must contain 'classifications' array",
                error_code="MISSING_CLASSIFICATIONS"
            )
        
        if not classifications_data:
            raise ValidationError(
                "Classifications array cannot be empty",
                error_code="EMPTY_CLASSIFICATIONS"
            )
        
        # Parse and validate each classification
        validated_items = []
        
        for i, item_data in enumerate(classifications_data):
            if not isinstance(item_data, dict):
                raise ValidationError(
                    f"Classification item {i} must be a dictionary",
                    error_code="INVALID_ITEM_TYPE"
                )
            
            try:
                # Create and validate classification item
                item = ClassificationItem(
                    quote=str(item_data.get('quote', '')),
                    label=str(item_data.get('label', '')),
                    confidence=float(item_data.get('confidence', 0.0))
                )
                
                # Additional label validation if expected labels provided
                if expected_labels and item.label not in expected_labels:
                    raise ValidationError(
                        f"Label '{item.label}' not in expected labels: {expected_labels}",
                        error_code="UNEXPECTED_LABEL"
                    )
                
                validated_items.append(item)
                
            except (ValueError, TypeError) as e:
                raise ValidationError(
                    f"Invalid classification item {i}: {str(e)}",
                    error_code="INVALID_CLASSIFICATION_ITEM"
                ) from e
        
        logger.debug(f"Validated {len(validated_items)} classification items")
        return validated_items
    
    def parse_batch_response_line(self, jsonl_line: str) -> Optional[List[ClassificationItem]]:
        """
        Parse a single line from batch JSONL response.
        
        Args:
            jsonl_line: Single line from JSONL response
            
        Returns:
            List of classification items or None if line is invalid
        """
        line = jsonl_line.strip()
        if not line:
            return None
        
        try:
            # Parse the JSONL line
            response_obj = json.loads(line)
            
            # Navigate OpenAI's response structure
            body = response_obj.get('response', {}).get('body', {})
            outputs = body.get('output', []) or []
            
            # Find the message output
            message_output = next((
                output for output in outputs 
                if output.get('type') == 'message'
            ), None)
            
            if not message_output:
                logger.warning("No message output found in response line")
                return None
            
            # Extract text content
            content_list = message_output.get('content', []) or []
            text_content = next((
                content for content in content_list
                if content.get('type') == 'output_text' and 'text' in content
            ), None)
            
            if not text_content:
                logger.warning("No text content found in message output")
                return None
            
            # Parse the classification JSON
            classification_data = json.loads(text_content['text'])
            
            # Validate and return classifications
            return self.validate_classification_response(classification_data)
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error in batch response line: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error parsing batch response line: {e}")
            return None
    
    def parse_batch_response_jsonl(self, jsonl_content: str) -> List[ClassificationItem]:
        """
        Parse complete JSONL batch response content.
        
        Args:
            jsonl_content: Complete JSONL response content
            
        Returns:
            List of all classification items from the batch
            
        Raises:
            ValidationError: If no valid classifications found
        """
        logger.info("Parsing batch JSONL response")
        
        all_classifications = []
        processed_lines = 0
        successful_lines = 0
        
        for line_num, line in enumerate(jsonl_content.splitlines(), 1):
            processed_lines += 1
            
            classifications = self.parse_batch_response_line(line)
            if classifications:
                all_classifications.extend(classifications)
                successful_lines += 1
        
        logger.info(
            f"Processed {processed_lines} lines, "
            f"{successful_lines} successful, "
            f"{len(all_classifications)} total classifications"
        )
        
        if not all_classifications:
            raise ValidationError(
                "No valid classifications found in batch response",
                error_code="NO_VALID_CLASSIFICATIONS"
            )
        
        return all_classifications
