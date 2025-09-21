"""
Professional main entry point for the Codebook text classification application.

This script provides a clean command-line interface for both interactive and
batch text classification using OpenAI's API with proper error handling,
logging, and user feedback.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List
import argparse
import time

# Configure logging before importing our modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Optional: Add file handler for debugging
        # logging.FileHandler('codebook.log')
    ]
)

# Set third-party logging to WARNING to reduce noise
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Import our modules
try:
    from core.config import get_config
    from core.exceptions import CodebookError, ConfigurationError
    from services.classification_service import ClassificationService
    from models.classification import ClassificationItem
except ImportError as e:
    print(f"Failed to import required modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class CodebookCLI:
    """
    Command-line interface for the Codebook application.
    
    Provides an interactive menu system for text classification operations
    with professional error handling and user feedback.
    """
    
    def __init__(self):
        """Initialize the CLI with configuration and services."""
        try:
            self.config = get_config()
            self.classification_service = ClassificationService(self.config)
            logger.info("Codebook CLI initialized successfully")
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e.message}")
            print(f"\nConfiguration Error: {e.message}")
            print("\nPlease check your configuration:")
            print("1. Copy .env.example to .env")
            print("2. Set your OPENAI_API_KEY in the .env file")
            print("3. Ensure all required dependencies are installed")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            print(f"\nFailed to initialize application: {str(e)}")
            sys.exit(1)
    
    def display_main_menu(self) -> None:
        """Display the main menu options."""
        print("\n" + "="*60)
        print("           CODEBOOK - Text Classification Tool")
        print("="*60)
        print("\nChoose an operation:")
        print("1. Live Classification (immediate results)")
        print("2. Batch Classification (submit job, retrieve later)")
        print("3. Check Batch Status")
        print("4. Retrieve Batch Results")
        print("5. List Recent Batch Jobs")
        print("6. Cancel Batch Job")
        print("7. View API Usage Statistics")
        print("8. Help & Documentation")
        print("9. Exit")
        print("-"*60)
    
    def get_user_choice(self, prompt: str, valid_choices: List[str]) -> str:
        """
        Get and validate user input.
        
        Args:
            prompt: Prompt to display to user
            valid_choices: List of valid input options
            
        Returns:
            Validated user choice
        """
        while True:
            choice = input(prompt).strip().lower()
            if choice in valid_choices:
                return choice
            print(f"Invalid choice. Please enter one of: {', '.join(valid_choices)}")
    
    def load_data_files(self) -> tuple[List[str], List[str]]:
        """
        Load labels and texts from CSV files using GUI.
        
        Returns:
            Tuple of (labels, texts)
            
        Raises:
            CodebookError: If file loading fails
        """
        print("\nLoading data files...")
        print("1. First, select your labels CSV file")
        
        try:
            # Load labels
            labels = self.classification_service.load_labels_from_file()
            print(f"✓ Loaded {len(labels)} unique labels: {', '.join(labels[:5])}{'...' if len(labels) > 5 else ''}")
            
            # For texts, we need to use a file path since GUI text loading isn't implemented yet
            print("\n2. Next, select your texts CSV file")
            print("   (Note: Currently requires file path input)")
            
            text_file_path = input("Enter path to texts CSV file: ").strip()
            if not text_file_path:
                raise CodebookError("No text file path provided", error_code="NO_TEXT_FILE")
            
            text_path = Path(text_file_path)
            if not text_path.exists():
                raise CodebookError(f"Text file not found: {text_path}", error_code="FILE_NOT_FOUND")
            
            # Ask about headers
            has_headers = self.get_user_choice(
                "Does the CSV file have headers? (y/n): ",
                ['y', 'yes', 'n', 'no']
            ).startswith('y')
            
            texts = self.classification_service.load_texts_from_file(
                file_path=text_path,
                has_headers=has_headers
            )
            
            print(f"✓ Loaded {len(texts)} texts for classification")
            
            return labels, texts
            
        except CodebookError:
            raise
        except Exception as e:
            raise CodebookError(f"Failed to load data files: {str(e)}", error_code="FILE_LOAD_ERROR") from e
    
    def run_live_classification(self) -> None:
        """Run live classification workflow."""
        print("\n" + "="*50)
        print("         LIVE CLASSIFICATION")
        print("="*50)
        
        try:
            # Load data
            labels, texts = self.load_data_files()
            
            print(f"\nReady to classify {len(texts)} texts using {len(labels)} labels")
            print("This will make individual API calls for each text.")
            
            proceed = self.get_user_choice(
                f"Proceed with live classification? (y/n): ",
                ['y', 'yes', 'n', 'no']
            )
            
            if not proceed.startswith('y'):
                print("Live classification cancelled.")
                return
            
            # Progress tracking
            def progress_callback(current: int, total: int, text_preview: str):
                percent = (current / total) * 100
                print(f"Progress: {current}/{total} ({percent:.1f}%) - {text_preview}")
            
            print(f"\nStarting classification...")
            start_time = time.time()
            
            # Perform classification
            responses = self.classification_service.classify_texts_live(
                texts=texts,
                allowed_labels=labels,
                progress_callback=progress_callback
            )
            
            # Extract all classifications
            all_classifications = []
            for response in responses:
                all_classifications.extend(response.classifications)
            
            duration = time.time() - start_time
            print(f"\n✓ Classification completed in {duration:.2f} seconds")
            print(f"✓ Processed {len(all_classifications)} classifications")
            
            # Save results
            saved_path = self.classification_service.save_classifications_to_file(
                classifications=all_classifications,
                use_gui=True
            )
            
            if saved_path:
                print(f"✓ Results saved to: {saved_path}")
            else:
                print("Results not saved (cancelled by user)")
                
        except CodebookError as e:
            logger.error(f"Live classification failed: {e.message}")
            print(f"\nError: {e.message}")
        except KeyboardInterrupt:
            print("\nClassification interrupted by user.")
        except Exception as e:
            logger.error(f"Unexpected error in live classification: {str(e)}")
            print(f"\nUnexpected error: {str(e)}")
    
    def run_batch_classification(self) -> None:
        """Run batch classification workflow."""
        print("\n" + "="*50)
        print("         BATCH CLASSIFICATION")
        print("="*50)
        
        try:
            # Load data
            labels, texts = self.load_data_files()
            
            print(f"\nReady to submit batch job for {len(texts)} texts using {len(labels)} labels")
            print("Batch jobs are processed asynchronously by OpenAI.")
            print("You can check status and retrieve results later.")
            
            proceed = self.get_user_choice(
                f"Submit batch job? (y/n): ",
                ['y', 'yes', 'n', 'no']
            )
            
            if not proceed.startswith('y'):
                print("Batch submission cancelled.")
                return
            
            print(f"\nSubmitting batch job...")
            
            batch_id = self.classification_service.submit_batch_classification(
                texts=texts,
                allowed_labels=labels,
                description=f"codebook_classification_{len(texts)}_items"
            )
            
            print(f"\n✓ Batch job submitted successfully!")
            print(f"✓ Batch ID: {batch_id}")
            print(f"\nYou can check the status using option 3 in the main menu.")
            print(f"Batch jobs typically complete within 24 hours.")
            
        except CodebookError as e:
            logger.error(f"Batch submission failed: {e.message}")
            print(f"\nError: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error in batch submission: {str(e)}")
            print(f"\nUnexpected error: {str(e)}")
    
    def check_batch_status(self) -> None:
        """Check the status of a batch job."""
        print("\n" + "="*50)
        print("         CHECK BATCH STATUS")
        print("="*50)
        
        batch_id = input("\nEnter batch ID: ").strip()
        if not batch_id:
            print("No batch ID provided.")
            return
        
        try:
            status_info = self.classification_service.get_batch_status(batch_id)
            
            print(f"\nBatch Status for {batch_id}:")
            print(f"Status: {status_info['status']}")
            print(f"Created: {status_info['created_at']}")
            
            if status_info.get('completed_at'):
                print(f"Completed: {status_info['completed_at']}")
            
            if status_info.get('request_counts'):
                counts = status_info['request_counts']
                print(f"Request Counts: {counts}")
            
            if status_info.get('metadata'):
                print(f"Metadata: {status_info['metadata']}")
            
            if status_info['status'] == 'completed':
                print(f"\n✓ Batch is complete! You can retrieve results using option 4.")
            elif status_info['status'] == 'failed':
                print(f"\n✗ Batch failed. Check the OpenAI dashboard for details.")
            else:
                print(f"\n⏳ Batch is still processing. Check back later.")
                
        except CodebookError as e:
            print(f"\nError checking batch status: {e.message}")
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
    
    def retrieve_batch_results(self) -> None:
        """Retrieve results from a completed batch job."""
        print("\n" + "="*50)
        print("         RETRIEVE BATCH RESULTS")
        print("="*50)
        
        batch_id = input("\nEnter batch ID: ").strip()
        if not batch_id:
            print("No batch ID provided.")
            return
        
        try:
            print(f"\nRetrieving results for batch: {batch_id}")
            
            classifications = self.classification_service.retrieve_batch_results(batch_id)
            
            print(f"✓ Retrieved {len(classifications)} classification results")
            
            # Show sample results
            if classifications:
                print(f"\nSample results:")
                for i, item in enumerate(classifications[:3], 1):
                    text_preview = item.quote[:50] + "..." if len(item.quote) > 50 else item.quote
                    print(f"{i}. \"{text_preview}\" → {item.label} (confidence: {item.confidence:.3f})")
                
                if len(classifications) > 3:
                    print(f"... and {len(classifications) - 3} more results")
            
            # Save results
            saved_path = self.classification_service.save_classifications_to_file(
                classifications=classifications,
                use_gui=True
            )
            
            if saved_path:
                print(f"✓ Results saved to: {saved_path}")
            else:
                print("Results not saved (cancelled by user)")
                
        except CodebookError as e:
            print(f"\nError retrieving batch results: {e.message}")
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
    
    def list_batch_jobs(self) -> None:
        """List recent batch jobs."""
        print("\n" + "="*50)
        print("         RECENT BATCH JOBS")
        print("="*50)
        
        try:
            jobs = self.classification_service.list_batch_jobs(limit=10)
            
            if not jobs:
                print("\nNo batch jobs found.")
                return
            
            print(f"\nFound {len(jobs)} recent batch jobs:")
            print("-" * 80)
            print(f"{'ID':<30} {'Status':<12} {'Created':<20} {'Description'}")
            print("-" * 80)
            
            for job in jobs:
                job_id = job['id'][:28] + "..." if len(job['id']) > 30 else job['id']
                status = job.get('status', 'unknown')
                created = job.get('created_at', 'unknown')
                description = job.get('metadata', {}).get('description', 'no description')[:20]
                
                print(f"{job_id:<30} {status:<12} {created:<20} {description}")
            
        except CodebookError as e:
            print(f"\nError listing batch jobs: {e.message}")
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
    
    def cancel_batch_job(self) -> None:
        """Cancel a batch job."""
        print("\n" + "="*50)
        print("         CANCEL BATCH JOB")
        print("="*50)
        
        batch_id = input("\nEnter batch ID to cancel: ").strip()
        if not batch_id:
            print("No batch ID provided.")
            return
        
        confirm = self.get_user_choice(
            f"Are you sure you want to cancel batch {batch_id}? (y/n): ",
            ['y', 'yes', 'n', 'no']
        )
        
        if not confirm.startswith('y'):
            print("Cancellation aborted.")
            return
        
        try:
            success = self.classification_service.cancel_batch_job(batch_id)
            
            if success:
                print(f"✓ Batch {batch_id} cancelled successfully.")
            else:
                print(f"✗ Failed to cancel batch {batch_id}. It may already be completed or failed.")
                
        except CodebookError as e:
            print(f"\nError cancelling batch job: {e.message}")
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
    
    def show_api_usage_stats(self) -> None:
        """Display API usage statistics."""
        print("\n" + "="*50)
        print("         API USAGE STATISTICS")
        print("="*50)
        
        try:
            stats = self.classification_service.get_api_usage_stats()
            
            print(f"\nCurrent session statistics:")
            print(f"Requests made: {stats['requests_made']}")
            print(f"Tokens used: {stats['tokens_used']}")
            print(f"Errors encountered: {stats['errors_encountered']}")
            print(f"Estimated cost: ${stats['estimated_cost']:.4f}")
            
            if stats['requests_made'] == 0:
                print("\nNo API requests made in this session yet.")
            
        except Exception as e:
            print(f"\nError retrieving usage statistics: {str(e)}")
    
    def show_help(self) -> None:
        """Display help and documentation."""
        print("\n" + "="*60)
        print("              HELP & DOCUMENTATION")
        print("="*60)
        
        help_text = """
OVERVIEW:
Codebook is a professional text classification tool using OpenAI's API.
It supports both live (immediate) and batch (asynchronous) processing.

OPERATION MODES:

1. Live Classification:
   - Processes texts immediately with real-time results
   - Best for small datasets (< 100 texts)
   - Higher cost per classification
   - Immediate feedback and results

2. Batch Classification:
   - Submits jobs to OpenAI's batch queue
   - Best for large datasets (100+ texts)
   - 50% cost reduction compared to live
   - Results available within 24 hours

FILE FORMATS:
- Labels CSV: Single column with classification labels
- Texts CSV: Text data in first column (other columns ignored)
- Both files can optionally have headers

CONFIGURATION:
- Copy .env.example to .env
- Set your OPENAI_API_KEY in the .env file
- Customize model and other settings as needed

TROUBLESHOOTING:
- Ensure your OpenAI API key has sufficient credits
- Check file formats match expected CSV structure
- For large batches, monitor status regularly
- Contact support if jobs fail unexpectedly

For more information, see the README.md file.
        """
        print(help_text)
    
    def run(self) -> None:
        """Run the main CLI loop."""
        print("Welcome to Codebook - Professional Text Classification Tool")
        print(f"Configuration loaded successfully. Using model: {self.config.default_model}")
        
        while True:
            try:
                self.display_main_menu()
                
                choice = input("\nEnter your choice (1-9): ").strip()
                
                if choice == '1':
                    self.run_live_classification()
                elif choice == '2':
                    self.run_batch_classification()
                elif choice == '3':
                    self.check_batch_status()
                elif choice == '4':
                    self.retrieve_batch_results()
                elif choice == '5':
                    self.list_batch_jobs()
                elif choice == '6':
                    self.cancel_batch_job()
                elif choice == '7':
                    self.show_api_usage_stats()
                elif choice == '8':
                    self.show_help()
                elif choice == '9':
                    print("\nThank you for using Codebook!")
                    break
                else:
                    print("\nInvalid choice. Please enter a number from 1 to 9.")
                
                # Pause before showing menu again
                if choice != '9':
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nExiting Codebook. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                print(f"\nUnexpected error: {str(e)}")
                print("Please try again or exit the application.")


def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Codebook - Professional Text Classification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run interactive mode
  python main.py --help            # Show this help message

For more information, see the README.md file.
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Codebook 2.0.0 - Professional Edition'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Run the application
    try:
        cli = CodebookCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"\nFatal error: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
