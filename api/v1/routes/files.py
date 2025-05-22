"""
File API Routes

This module provides API routes for file operations, including:
- File upload and processing
- LLM processing of file contents
"""
import io
import os
from flask import Blueprint, Response, current_app, jsonify, request
from api.v1.schemas.files import FileUploadRequest, FileProcessRequest
from core.auth import auth_required
from utils.file_processing.processor import FileProcessor
from werkzeug.utils import secure_filename

# Create a blueprint for the file routes
bp = Blueprint('files', __name__, url_prefix='/files')

# Initialize logger
from core.logging import get_logger
logger = get_logger(__name__)

@bp.route('/upload', methods=['POST'])
@auth_required
def upload_file():
    """
    Upload and process a file.

    Returns:
        Processed file contents
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({
            'error': 'No file provided',
            'details': 'Please upload a file using multipart/form-data',
            'code': 'NO_FILE'
        }), 400

    file = request.files['file']

    # Check if file was selected
    if file.filename == '':
        return jsonify({
            'error': 'No file selected',
            'details': 'Please select a file to upload',
            'code': 'NO_FILE_SELECTED'
        }), 400

    # Process the file
    try:
        # Initialize file processor with settings from config
        file_processor = FileProcessor(
            max_file_size_mb=current_app.config.get('SETTINGS').max_file_size_mb
        )
        
        filename = secure_filename(file.filename)
        contents = file_processor.process_file(file, filename)

        # Return processed contents
        return jsonify({
            'contents': contents.dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({
            'error': 'File Processing Error',
            'details': str(e),
            'code': 'FILE_PROCESSING_ERROR'
        }), 400

@bp.route('/process', methods=['POST'])
@auth_required
def process_file_with_llm():
    """
    Process a file with LLM.

    Returns:
        LLM processing result
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({
            'error': 'No file provided',
            'details': 'Please upload a file using multipart/form-data',
            'code': 'NO_FILE'
        }), 400

    file = request.files['file']

    # Check if file was selected
    if file.filename == '':
        return jsonify({
            'error': 'No file selected',
            'details': 'Please select a file to upload',
            'code': 'NO_FILE_SELECTED'
        }), 400

    # Get processing parameters
    prompt_prefix = request.form.get('prompt_prefix', 'Summarize the following content:')
    max_tokens = int(request.form.get('max_tokens', 500))

    # Process the file
    try:
        # Initialize file processor with settings from config
        file_processor = FileProcessor(
            max_file_size_mb=current_app.config.get('SETTINGS').max_file_size_mb
        )
        
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
        from llm.factory import get_llm_handler
        llm_handler = get_llm_handler(current_app.config.get("SETTINGS"))
        result = llm_handler.process_prompt(
            prompt=prompt,
            max_tokens=max_tokens
        )

        # Return result along with file metadata
        return jsonify({
            'result': result,
            'metadata': contents.metadata.dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing file with LLM: {str(e)}")
        return jsonify({
            'error': 'Server Error',
            'details': str(e),
            'code': 'SERVER_ERROR'
        }), 500
