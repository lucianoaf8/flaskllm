# api/v1/routes.py
import io
import os
from flask import request, current_app
from werkzeug.utils import secure_filename

from core.exceptions import FileProcessingError
from utils.file_processor import FileProcessor

# Initialize file processor
file_processor = FileProcessor(
    max_file_size_mb=current_app.config.get('MAX_FILE_SIZE_MB', 10)
)

@api_v1.route('/files/upload', methods=['POST'])
@require_api_token
def upload_file():
    """
    Upload and process a file.

    Returns:
        Processed file contents
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return {
            'error': 'No file provided',
            'details': 'Please upload a file using multipart/form-data',
            'code': 'NO_FILE'
        }, 400

    file = request.files['file']

    # Check if file was selected
    if file.filename == '':
        return {
            'error': 'No file selected',
            'details': 'Please select a file to upload',
            'code': 'NO_FILE_SELECTED'
        }, 400

    # Process the file
    try:
        filename = secure_filename(file.filename)
        contents = file_processor.process_file(file, filename)

        # Convert Pydantic models to dictionaries
        return {
            'contents': contents.dict()
        }
    except FileProcessingError as e:
        return {
            'error': 'File Processing Error',
            'details': str(e),
            'code': 'FILE_PROCESSING_ERROR'
        }, 400
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return {
            'error': 'Server Error',
            'details': str(e),
            'code': 'SERVER_ERROR'
        }, 500

@api_v1.route('/files/process', methods=['POST'])
@require_api_token
def process_file_with_llm():
    """
    Process a file with LLM.

    Returns:
        LLM processing result
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return {
            'error': 'No file provided',
            'details': 'Please upload a file using multipart/form-data',
            'code': 'NO_FILE'
        }, 400

    file = request.files['file']

    # Check if file was selected
    if file.filename == '':
        return {
            'error': 'No file selected',
            'details': 'Please select a file to upload',
            'code': 'NO_FILE_SELECTED'
        }, 400

    # Get processing parameters
    prompt_prefix = request.form.get('prompt_prefix', 'Summarize the following content:')
    max_tokens = int(request.form.get('max_tokens', 500))

    # Process the file
    try:
        filename = secure_filename(file.filename)
        contents = file_processor.process_file(file, filename)

        # Truncate text if too long (avoid token limits)
        text = contents.text
        max_chars = 4000  # Adjust based on typical token/char ratio
        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"

        # Create prompt
        prompt = f"{prompt_prefix}\n\n{text}"

        # Process with LLM
        llm_handler = get_llm_handler()
        result = llm_handler.process_prompt(
            prompt=prompt,
            max_tokens=max_tokens
        )

        # Return result along with file metadata
        return {
            'result': result,
            'metadata': contents.metadata.dict()
        }
    except FileProcessingError as e:
        return {
            'error': 'File Processing Error',
            'details': str(e),
            'code': 'FILE_PROCESSING_ERROR'
        }, 400
    except Exception as e:
        logger.error(f"Error processing file with LLM: {str(e)}", exc_info=True)
        return {
            'error': 'Server Error',
            'details': str(e),
            'code': 'SERVER_ERROR'
        }, 500
