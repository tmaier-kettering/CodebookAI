"""
Professional CSV file handling with comprehensive error handling and validation.

This module provides a robust CSV handler that:
- Validates file formats and content
- Provides clear error messages and user feedback
- Handles GUI operations safely with fallbacks
- Uses proper resource management
- Follows professional coding standards
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict
from contextlib import contextmanager
import io

from core.exceptions import FileProcessingError, ValidationError
from models.classification import ClassificationItem, ClassificationResponse

# Set up logger for this module
logger = logging.getLogger(__name__)


class CSVHandler:
    """
    Professional CSV file handler with robust error handling and validation.
    
    This class provides methods for reading and writing CSV files related to
    text classification, with comprehensive error handling and user feedback.
    """
    
    def __init__(self, encoding: str = 'utf-8') -> None:
        """
        Initialize the CSV handler.
        
        Args:
            encoding: Character encoding to use for file operations
        """
        self.encoding = encoding
        logger.debug(f"CSVHandler initialized with encoding: {encoding}")
    
    @contextmanager
    def _safe_file_operation(self, file_path: Path, mode: str):
        """
        Context manager for safe file operations with proper error handling.
        
        Args:
            file_path: Path to the file
            mode: File open mode
            
        Yields:
            File handle
            
        Raises:
            FileProcessingError: If file operation fails
        """
        try:
            with open(file_path, mode, encoding=self.encoding, newline='') as file:
                yield file
        except FileNotFoundError:
            raise FileProcessingError(
                f"File not found: {file_path}",
                error_code="FILE_NOT_FOUND",
                context={"file_path": str(file_path)}
            )
        except PermissionError:
            raise FileProcessingError(
                f"Permission denied accessing file: {file_path}",
                error_code="PERMISSION_DENIED",
                context={"file_path": str(file_path)}
            )
        except UnicodeDecodeError as e:
            raise FileProcessingError(
                f"File encoding error in {file_path}: {str(e)}",
                error_code="ENCODING_ERROR",
                context={"file_path": str(file_path), "encoding": self.encoding}
            )
        except Exception as e:
            raise FileProcessingError(
                f"Unexpected error accessing file {file_path}: {str(e)}",
                error_code="FILE_OPERATION_FAILED",
                context={"file_path": str(file_path)}
            ) from e
    
    def read_labels_from_csv(
        self, 
        file_path: Path, 
        has_headers: bool = False,
        column_index: int = 0
    ) -> List[str]:
        """
        Read labels from a CSV file with validation and error handling.
        
        Args:
            file_path: Path to the CSV file
            has_headers: Whether the file has header row
            column_index: Which column to read labels from (0-based)
            
        Returns:
            List of cleaned, non-empty labels
            
        Raises:
            FileProcessingError: If file cannot be read or processed
            ValidationError: If file format is invalid or contains no data
        """
        logger.info(f"Reading labels from CSV: {file_path}")
        
        if not file_path.exists():
            raise FileProcessingError(
                f"CSV file does not exist: {file_path}",
                error_code="FILE_NOT_FOUND"
            )
        
        labels = []
        
        with self._safe_file_operation(file_path, 'r') as file:
            try:
                reader = csv.reader(file)
                rows = list(reader)
                
                if not rows:
                    raise ValidationError(
                        f"CSV file is empty: {file_path}",
                        error_code="EMPTY_FILE"
                    )
                
                # Skip header row if present
                data_rows = rows[1:] if has_headers else rows
                
                if not data_rows:
                    raise ValidationError(
                        "No data rows found after header row",
                        error_code="NO_DATA_ROWS"
                    )
                
                # Extract labels from specified column
                for row_num, row in enumerate(data_rows, start=2 if has_headers else 1):
                    if not row:  # Skip empty rows
                        continue
                        
                    if len(row) <= column_index:
                        logger.warning(
                            f"Row {row_num} has insufficient columns, skipping"
                        )
                        continue
                    
                    label = str(row[column_index]).strip()
                    if label:  # Only add non-empty labels
                        labels.append(label)
                
                if not labels:
                    raise ValidationError(
                        f"No valid labels found in column {column_index}",
                        error_code="NO_VALID_LABELS"
                    )
                
                # Remove duplicates while preserving order
                unique_labels = []
                seen = set()
                for label in labels:
                    if label not in seen:
                        unique_labels.append(label)
                        seen.add(label)
                
                logger.info(f"Successfully read {len(unique_labels)} unique labels")
                return unique_labels
                
            except csv.Error as e:
                raise FileProcessingError(
                    f"CSV parsing error in {file_path}: {str(e)}",
                    error_code="CSV_PARSE_ERROR"
                ) from e
    
    def read_texts_from_csv(
        self, 
        file_path: Path, 
        has_headers: bool = False,
        text_column: int = 0
    ) -> List[str]:
        """
        Read text data from a CSV file for classification.
        
        Args:
            file_path: Path to the CSV file
            has_headers: Whether the file has header row
            text_column: Which column contains the text (0-based)
            
        Returns:
            List of text strings to classify
            
        Raises:
            FileProcessingError: If file cannot be read or processed
            ValidationError: If file format is invalid or contains no data
        """
        logger.info(f"Reading texts from CSV: {file_path}")
        
        texts = []
        
        with self._safe_file_operation(file_path, 'r') as file:
            try:
                reader = csv.reader(file)
                rows = list(reader)
                
                if not rows:
                    raise ValidationError(
                        f"CSV file is empty: {file_path}",
                        error_code="EMPTY_FILE"
                    )
                
                # Skip header row if present
                data_rows = rows[1:] if has_headers else rows
                
                if not data_rows:
                    raise ValidationError(
                        "No data rows found after header row",
                        error_code="NO_DATA_ROWS"
                    )
                
                # Extract texts from specified column
                for row_num, row in enumerate(data_rows, start=2 if has_headers else 1):
                    if not row:  # Skip empty rows
                        continue
                        
                    if len(row) <= text_column:
                        logger.warning(
                            f"Row {row_num} has insufficient columns, skipping"
                        )
                        continue
                    
                    text = str(row[text_column]).strip()
                    if text:  # Only add non-empty texts
                        texts.append(text)
                
                if not texts:
                    raise ValidationError(
                        f"No valid texts found in column {text_column}",
                        error_code="NO_VALID_TEXTS"
                    )
                
                logger.info(f"Successfully read {len(texts)} texts")
                return texts
                
            except csv.Error as e:
                raise FileProcessingError(
                    f"CSV parsing error in {file_path}: {str(e)}",
                    error_code="CSV_PARSE_ERROR"
                ) from e
    
    def write_classifications_to_csv(
        self,
        classifications: List[ClassificationItem],
        file_path: Path,
        include_headers: bool = True
    ) -> None:
        """
        Write classification results to a CSV file.
        
        Args:
            classifications: List of classification results
            file_path: Path where to save the CSV file
            include_headers: Whether to include header row
            
        Raises:
            FileProcessingError: If file cannot be written
            ValidationError: If classification data is invalid
        """
        if not classifications:
            raise ValidationError(
                "No classifications provided to write",
                error_code="NO_DATA_TO_WRITE"
            )
        
        logger.info(f"Writing {len(classifications)} classifications to: {file_path}")
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._safe_file_operation(file_path, 'w') as file:
            try:
                writer = csv.writer(file)
                
                # Write headers if requested
                if include_headers:
                    writer.writerow(['text', 'label', 'confidence'])
                
                # Write classification data
                for item in classifications:
                    writer.writerow([
                        item.quote,
                        item.label,
                        f"{item.confidence:.6f}"  # Format confidence to 6 decimal places
                    ])
                
                logger.info(f"Successfully wrote classifications to {file_path}")
                
            except csv.Error as e:
                raise FileProcessingError(
                    f"CSV writing error: {str(e)}",
                    error_code="CSV_WRITE_ERROR"
                ) from e
    
    def parse_batch_results_from_jsonl_bytes(self, content_bytes: bytes) -> List[ClassificationItem]:
        """
        Parse OpenAI batch results from JSONL bytes into classification items.
        
        This method processes the JSONL response from OpenAI's batch API and
        extracts classification results.
        
        Args:
            content_bytes: Raw bytes from OpenAI batch response
            
        Returns:
            List of parsed classification items
            
        Raises:
            FileProcessingError: If parsing fails
        """
        logger.info("Parsing batch results from JSONL bytes")
        
        try:
            # Decode bytes to text
            jsonl_text = content_bytes.decode('utf-8', errors='replace')
            
            classifications = []
            
            for line_num, raw_line in enumerate(jsonl_text.splitlines(), 1):
                line = raw_line.strip()
                if not line:
                    continue
                
                try:
                    import json
                    obj = json.loads(line)
                    
                    # Navigate the OpenAI response structure
                    body = obj.get('response', {}).get('body', {})
                    outputs = body.get('output', []) or []
                    
                    # Find the message output
                    msg = next((o for o in outputs if o.get('type') == 'message'), None)
                    if not msg:
                        logger.warning(f"No message found in line {line_num}, skipping")
                        continue
                    
                    # Extract the text content
                    content_list = msg.get('content', []) or []
                    text_chunk = next((
                        c for c in content_list 
                        if c.get('type') == 'output_text' and 'text' in c
                    ), None)
                    
                    if not text_chunk:
                        logger.warning(f"No text content found in line {line_num}, skipping")
                        continue
                    
                    # Parse the classification JSON
                    payload = json.loads(text_chunk['text'])
                    
                    # Extract classifications
                    for classification_data in payload.get('classifications', []):
                        try:
                            item = ClassificationItem(
                                quote=classification_data.get('quote', ''),
                                label=classification_data.get('label', ''),
                                confidence=float(classification_data.get('confidence', 0.0))
                            )
                            classifications.append(item)
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Skipping invalid classification data: {e}")
                            continue
                
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error on line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing line {line_num}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(classifications)} classifications")
            return classifications
            
        except UnicodeDecodeError as e:
            raise FileProcessingError(
                f"Failed to decode batch results: {str(e)}",
                error_code="DECODE_ERROR"
            ) from e
        except Exception as e:
            raise FileProcessingError(
                f"Failed to parse batch results: {str(e)}",
                error_code="PARSE_ERROR"
            ) from e
    
    def import_csv_with_gui(
        self, 
        title: str = "Import CSV", 
        filetypes: Tuple[Tuple[str, str], ...] = (("CSV files", "*.csv"), ("All files", "*.*"))
    ) -> Tuple[Optional[List[str]], Optional[Path]]:
        """
        Import CSV file using GUI dialog with professional error handling.
        
        This method provides a user-friendly interface for importing CSV files
        with proper validation and error reporting.
        
        Args:
            title: Title for the file dialog
            filetypes: File type filters for the dialog
            
        Returns:
            Tuple of (labels_list, file_path) or (None, None) if cancelled
            
        Raises:
            FileProcessingError: If GUI operations fail
        """
        logger.info(f"Opening CSV import dialog: {title}")
        
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            
            # Create main window (hidden)
            root = tk.Tk()
            root.withdraw()
            root.title(title)
            
            # Variables for storing user input
            selected_file = None
            has_headers = tk.BooleanVar(value=False)
            result_labels = None
            
            def browse_file():
                nonlocal selected_file
                file_path = filedialog.askopenfilename(
                    title=title,
                    filetypes=list(filetypes)
                )
                if file_path:
                    selected_file = Path(file_path)
                    file_entry.delete(0, tk.END)
                    file_entry.insert(0, str(selected_file))
            
            def process_file():
                nonlocal result_labels
                
                if not selected_file:
                    messagebox.showerror("Error", "No file selected.")
                    return
                
                try:
                    # Check if file has multiple columns and warn user
                    with self._safe_file_operation(selected_file, 'r') as file:
                        reader = csv.reader(file)
                        first_row = next(reader, [])
                        
                        if len(first_row) > 1:
                            proceed = messagebox.askokcancel(
                                "Multiple Columns Detected",
                                f"The CSV file has {len(first_row)} columns. "
                                "Only the first column will be used for labels. "
                                "Do you want to proceed?"
                            )
                            if not proceed:
                                return
                    
                    # Read labels from the file
                    result_labels = self.read_labels_from_csv(
                        selected_file,
                        has_headers=has_headers.get(),
                        column_index=0
                    )
                    
                    messagebox.showinfo(
                        "Success", 
                        f"Successfully imported {len(result_labels)} unique labels."
                    )
                    root.quit()
                    
                except (FileProcessingError, ValidationError) as e:
                    messagebox.showerror("Error", f"Failed to process file:\n{e.message}")
                except Exception as e:
                    messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
            
            # Create and configure the dialog
            dialog = tk.Toplevel(root)
            dialog.title(title)
            dialog.geometry("600x200")
            dialog.resizable(False, False)
            
            # Center the dialog
            dialog.transient(root)
            dialog.grab_set()
            
            # File selection frame
            file_frame = tk.Frame(dialog)
            file_frame.pack(pady=10, padx=20, fill=tk.X)
            
            tk.Label(file_frame, text="CSV File:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
            
            file_select_frame = tk.Frame(file_frame)
            file_select_frame.pack(fill=tk.X, pady=5)
            
            file_entry = tk.Entry(file_select_frame, font=("Arial", 10))
            file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            browse_button = tk.Button(
                file_select_frame, 
                text="Browse", 
                command=browse_file,
                font=("Arial", 10)
            )
            browse_button.pack(side=tk.RIGHT)
            
            # Options frame
            options_frame = tk.Frame(dialog)
            options_frame.pack(pady=10, padx=20, fill=tk.X)
            
            headers_checkbox = tk.Checkbutton(
                options_frame,
                text="File has headers (skip first row)",
                variable=has_headers,
                font=("Arial", 10)
            )
            headers_checkbox.pack(anchor=tk.W)
            
            # Buttons frame
            buttons_frame = tk.Frame(dialog)
            buttons_frame.pack(pady=20)
            
            process_button = tk.Button(
                buttons_frame,
                text="Import",
                command=process_file,
                font=("Arial", 10, "bold"),
                bg="#4CAF50",
                fg="white",
                padx=20
            )
            process_button.pack(side=tk.LEFT, padx=10)
            
            cancel_button = tk.Button(
                buttons_frame,
                text="Cancel",
                command=dialog.destroy,
                font=("Arial", 10),
                padx=20
            )
            cancel_button.pack(side=tk.LEFT, padx=10)
            
            # Run the dialog
            dialog.mainloop()
            
            # Clean up
            try:
                dialog.destroy()
                root.destroy()
            except tk.TclError:
                pass  # Already destroyed
            
            return result_labels, selected_file
            
        except ImportError:
            raise FileProcessingError(
                "GUI import requires tkinter, which is not available",
                error_code="GUI_NOT_AVAILABLE"
            )
        except Exception as e:
            raise FileProcessingError(
                f"GUI import failed: {str(e)}",
                error_code="GUI_IMPORT_FAILED"
            ) from e
    
    def save_csv_with_gui(
        self,
        classifications: List[ClassificationItem],
        default_filename: str = "classifications.csv"
    ) -> Optional[Path]:
        """
        Save classifications to CSV using GUI dialog.
        
        Args:
            classifications: Classification results to save
            default_filename: Default filename for save dialog
            
        Returns:
            Path to saved file or None if cancelled
            
        Raises:
            FileProcessingError: If save operation fails
        """
        if not classifications:
            raise ValidationError(
                "No classifications provided to save",
                error_code="NO_DATA_TO_SAVE"
            )
        
        logger.info("Opening CSV save dialog")
        
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
            
            # Create hidden root window
            root = tk.Tk()
            root.withdraw()
            
            # Open save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Classifications as CSV",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            root.destroy()
            
            if not file_path:
                logger.info("Save operation cancelled by user")
                return None
            
            # Save the file
            save_path = Path(file_path)
            self.write_classifications_to_csv(classifications, save_path)
            
            logger.info(f"Classifications saved to: {save_path}")
            return save_path
            
        except ImportError:
            raise FileProcessingError(
                "GUI save requires tkinter, which is not available",
                error_code="GUI_NOT_AVAILABLE"
            )
        except Exception as e:
            raise FileProcessingError(
                f"GUI save failed: {str(e)}",
                error_code="GUI_SAVE_FAILED"
            ) from e
