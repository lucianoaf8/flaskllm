# flaskllm/utils/file_processing/processor.py
"""
File Processing Utility Module

This module provides utilities for file operations such as reading, writing,
parsing, and processing different file formats (JSON, CSV, YAML, etc.)
"""

from typing import Any, Dict, List, Optional, BinaryIO
from werkzeug.datastructures import FileStorage
from core.exceptions import InvalidInputError
from core.logging import get_logger

import os
import json
import csv
import shutil
from pathlib import Path
from typing import Union, TextIO, Iterator

# Configure logger
logger = get_logger(__name__)

def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read a text file and return its contents as a string.
    
    Args:
        file_path: Path to the text file
        encoding: File encoding
        
    Returns:
        String containing the file contents
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        UnicodeDecodeError: If the file cannot be decoded with the specified encoding
    """
    logger.debug(f"Reading text file: {file_path}")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
        return content
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode file {file_path} with encoding {encoding}: {e}")
        raise


def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8', create_dirs: bool = True):
    """
    Write a string to a text file.
    
    Args:
        file_path: Path to the output file
        content: Content to write
        encoding: File encoding
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        IOError: If there's an error writing the file
    """
    logger.debug(f"Writing text file: {file_path}")
    
    file_path = Path(file_path)
    
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
    except IOError as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        raise


def read_json_file(file_path: Union[str, Path], encoding: str = 'utf-8'):
    """
    Read a JSON file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the JSON file
        encoding: File encoding
        
    Returns:
        Dictionary containing the JSON data
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    logger.debug(f"Reading JSON file: {file_path}")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            data = json.load(file)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {file_path}: {e}")
        raise


def write_json_file(
    file_path: Union[str, Path], 
    data: Dict[str, Any], 
    encoding: str = 'utf-8', 
    create_dirs: bool = True, 
    indent: int = 2
):
    """
    Write a dictionary to a JSON file.
    
    Args:
        file_path: Path to the output file
        data: Dictionary to write as JSON
        encoding: File encoding
        create_dirs: Whether to create parent directories if they don't exist
        indent: Number of spaces for indentation in the JSON file
        
    Raises:
        IOError: If there's an error writing the file
    """
    logger.debug(f"Writing JSON file: {file_path}")
    
    file_path = Path(file_path)
    
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding=encoding) as file:
            json.dump(data, file, indent=indent)
    except IOError as e:
        logger.error(f"Failed to write JSON file {file_path}: {e}")
        raise


def read_csv_file(
    file_path: Union[str, Path], 
    encoding: str = 'utf-8', 
    delimiter: str = ',', 
    has_header: bool = True
):
    """
    Read a CSV file and return its contents.
    
    Args:
        file_path: Path to the CSV file
        encoding: File encoding
        delimiter: CSV delimiter character
        has_header: Whether the first row contains column headers
        
    Returns:
        If has_header is True, a list of dictionaries mapping column names to values.
        If has_header is False, a list of lists containing row values.
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        csv.Error: If there's an error parsing the CSV
    """
    logger.debug(f"Reading CSV file: {file_path}")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding, newline='') as file:
            if has_header:
                reader = csv.DictReader(file, delimiter=delimiter)
                return list(reader)
            else:
                reader = csv.reader(file, delimiter=delimiter)
                return list(reader)
    except csv.Error as e:
        logger.error(f"Failed to parse CSV file {file_path}: {e}")
        raise


def write_csv_file(
    file_path: Union[str, Path], 
    data: Union[List[Dict[str, Any]], List[List[Any]]], 
    headers: Optional[List[str]] = None,
    encoding: str = 'utf-8', 
    delimiter: str = ',', 
    create_dirs: bool = True
):
    """
    Write data to a CSV file.
    
    Args:
        file_path: Path to the output CSV file
        data: Data to write (list of dictionaries or list of lists)
        headers: Column headers (required if data is a list of lists)
        encoding: File encoding
        delimiter: CSV delimiter character
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        ValueError: If data is a list of lists but no headers are provided
        IOError: If there's an error writing the file
    """
    logger.debug(f"Writing CSV file: {file_path}")
    
    file_path = Path(file_path)
    
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding=encoding, newline='') as file:
            # Check if data is a list of dictionaries or a list of lists
            if data and isinstance(data[0], dict):
                # Use the keys of the first dictionary as headers if none provided
                if headers is None:
                    headers = list(data[0].keys())
                
                writer = csv.DictWriter(file, fieldnames=headers, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            else:
                # For list of lists, headers must be provided
                if headers is None:
                    raise ValueError("Headers must be provided when writing a list of lists to CSV")
                
                writer = csv.writer(file, delimiter=delimiter)
                writer.writerow(headers)
                writer.writerows(data)
    except IOError as e:
        logger.error(f"Failed to write CSV file {file_path}: {e}")
        raise


def ensure_directory(directory_path: Union[str, Path]):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path object for the directory
        
    Raises:
        IOError: If the directory cannot be created
    """
    logger.debug(f"Ensuring directory exists: {directory_path}")
    
    directory_path = Path(directory_path)
    
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        return directory_path
    except IOError as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        raise


def list_files(
    directory_path: Union[str, Path], 
    pattern: str = "*", 
    recursive: bool = False,
    include_dirs: bool = False
):
    """
    List files in a directory matching a glob pattern.
    
    Args:
        directory_path: Path to the directory
        pattern: Glob pattern to match files
        recursive: Whether to search recursively
        include_dirs: Whether to include directories in the results
        
    Returns:
        List of Path objects for matching files
        
    Raises:
        FileNotFoundError: If the directory doesn't exist
    """
    logger.debug(f"Listing files in {directory_path} with pattern {pattern}")
    
    directory_path = Path(directory_path)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    # Use rglob for recursive search, glob for non-recursive
    glob_func = directory_path.rglob if recursive else directory_path.glob
    
    # Filter results based on include_dirs parameter
    if include_dirs:
        return sorted(glob_func(pattern))
    else:
        return sorted(p for p in glob_func(pattern) if p.is_file())


def copy_file(source_path: Union[str, Path], target_path: Union[str, Path], create_dirs: bool = True):
    """
    Copy a file from source to target.
    
    Args:
        source_path: Path to the source file
        target_path: Path to the target file
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        IOError: If there's an error copying the file
    """
    logger.debug(f"Copying file from {source_path} to {target_path}")
    
    source_path = Path(source_path)
    target_path = Path(target_path)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    if create_dirs and not target_path.parent.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.copy2(source_path, target_path)
    except IOError as e:
        logger.error(f"Failed to copy file from {source_path} to {target_path}: {e}")
        raise


def move_file(source_path: Union[str, Path], target_path: Union[str, Path], create_dirs: bool = True):
    """
    Move a file from source to target.
    
    Args:
        source_path: Path to the source file
        target_path: Path to the target file
        create_dirs: Whether to create parent directories if they don't exist
        
    Raises:
        FileNotFoundError: If the source file doesn't exist
        IOError: If there's an error moving the file
    """
    logger.debug(f"Moving file from {source_path} to {target_path}")
    
    source_path = Path(source_path)
    target_path = Path(target_path)
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    
    if create_dirs and not target_path.parent.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.move(source_path, target_path)
    except IOError as e:
        logger.error(f"Failed to move file from {source_path} to {target_path}: {e}")
        raise


def delete_file(file_path: Union[str, Path], ignore_missing: bool = False):
    """
    Delete a file.
    
    Args:
        file_path: Path to the file to delete
        ignore_missing: Whether to ignore if the file doesn't exist
        
    Returns:
        True if the file was deleted, False if it didn't exist and ignore_missing is True
        
    Raises:
        FileNotFoundError: If the file doesn't exist and ignore_missing is False
        IOError: If there's an error deleting the file
    """
    logger.debug(f"Deleting file: {file_path}")
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        if ignore_missing:
            logger.debug(f"File does not exist, ignoring: {file_path}")
            return False
        else:
            raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        file_path.unlink()
        return True
    except IOError as e:
        logger.error(f"Failed to delete file {file_path}: {e}")
        raise


class FileProcessor:
    """
    Class for handling file processing operations.
    
    Provides an object-oriented interface for working with files of various formats,
    including upload handling and format conversion.
    """
    
    def __init__(self, base_directory: Optional[Union[str, Path]] = None):
        """
        Initialize the file processor.
        
        Args:
            base_directory: Base directory for file operations (optional)
        """
        self.base_directory = Path(base_directory) if base_directory else None
        self.logger = logger
    
    def get_full_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Get the full path by joining with the base directory if set.
        
        Args:
            relative_path: Relative path
            
        Returns:
            Full path
        """
        path = Path(relative_path)
        if self.base_directory and not path.is_absolute():
            return self.base_directory / path
        return path
    
    def save_uploaded_file(
        self, 
        uploaded_file: FileStorage, 
        target_path: Union[str, Path], 
        create_dirs: bool = True,
        allowed_extensions: Optional[List[str]] = None
    ) -> Path:
        """
        Save an uploaded file to the target path.
        
        Args:
            uploaded_file: Uploaded file object
            target_path: Path where the file should be saved
            create_dirs: Whether to create parent directories if needed
            allowed_extensions: List of allowed file extensions (None for any)
            
        Returns:
            Path to the saved file
            
        Raises:
            InvalidInputError: If the file extension is not allowed
            IOError: If there's an error saving the file
        """
        full_path = self.get_full_path(target_path)
        
        # Check file extension if restrictions are provided
        if allowed_extensions:
            ext = Path(uploaded_file.filename).suffix.lower().lstrip('.')
            if ext not in allowed_extensions:
                raise InvalidInputError(
                    f"File extension '{ext}' not allowed. Allowed extensions: {', '.join(allowed_extensions)}"
                )
        
        # Create parent directories if needed
        if create_dirs:
            full_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"Saving uploaded file to {full_path}")
        
        try:
            uploaded_file.save(str(full_path))
            return full_path
        except Exception as e:
            self.logger.error(f"Failed to save uploaded file: {e}")
            raise IOError(f"Failed to save uploaded file: {e}")
    
    def read_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Read and return the contents of a text file."""
        return read_text_file(self.get_full_path(file_path), encoding)
    
    def write_file(self, file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> Path:
        """Write content to a text file."""
        full_path = self.get_full_path(file_path)
        write_text_file(full_path, content, encoding)
        return full_path
    
    def read_json(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> Dict[str, Any]:
        """Read and parse a JSON file."""
        return read_json_file(self.get_full_path(file_path), encoding)
    
    def write_json(self, file_path: Union[str, Path], data: Dict[str, Any], encoding: str = 'utf-8') -> Path:
        """Write data to a JSON file."""
        full_path = self.get_full_path(file_path)
        write_json_file(full_path, data, encoding=encoding)
        return full_path
    
    def read_csv(
        self, 
        file_path: Union[str, Path], 
        encoding: str = 'utf-8', 
        delimiter: str = ',',
        has_header: bool = True
    ) -> List[Any]:
        """Read and parse a CSV file."""
        return read_csv_file(
            self.get_full_path(file_path), 
            encoding=encoding, 
            delimiter=delimiter, 
            has_header=has_header
        )
    
    def write_csv(
        self,
        file_path: Union[str, Path],
        data: Union[List[Dict[str, Any]], List[List[Any]]],
        headers: Optional[List[str]] = None,
        encoding: str = 'utf-8',
        delimiter: str = ','
    ) -> Path:
        """Write data to a CSV file."""
        full_path = self.get_full_path(file_path)
        write_csv_file(
            full_path,
            data,
            headers=headers,
            encoding=encoding,
            delimiter=delimiter
        )
        return full_path
    
    def list_files(
        self, 
        directory_path: Optional[Union[str, Path]] = None, 
        pattern: str = '*',
        recursive: bool = False
    ) -> List[Path]:
        """List files in a directory matching a pattern."""
        dir_path = self.get_full_path(directory_path) if directory_path else self.base_directory
        if not dir_path:
            raise ValueError("No directory specified and no base directory set")
        return list_files(dir_path, pattern, recursive)
    
    def ensure_dir(self, directory_path: Optional[Union[str, Path]] = None) -> Path:
        """Ensure that a directory exists, creating it if necessary."""
        dir_path = self.get_full_path(directory_path) if directory_path else self.base_directory
        if not dir_path:
            raise ValueError("No directory specified and no base directory set")
        return ensure_directory(dir_path)
