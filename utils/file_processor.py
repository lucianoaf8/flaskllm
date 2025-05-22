# flaskllm/utils/file_processor.py
"""
File Processing Utility Module

This module provides utilities for file operations such as reading, writing,
parsing, and processing different file formats (JSON, CSV, YAML, etc.)
"""

import os
import json
import csv
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TextIO, Iterator

from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
    """
    Read a text file and return its contents as a string.
    
    Args:
        file_path: Path to the text file
        encoding: File encoding
        
    Returns:
        File contents as a string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        file_path = Path(file_path)
        logger.debug(f"Reading text file: {file_path}")
        
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
            
        logger.debug(f"Successfully read {len(content)} characters from {file_path}")
        return content
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise

def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8', create_dirs: bool = True) -> None:
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
    try:
        file_path = Path(file_path)
        logger.debug(f"Writing to text file: {file_path}")
        
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
            
        logger.debug(f"Successfully wrote {len(content)} characters to {file_path}")
    except IOError as e:
        logger.error(f"Error writing to file {file_path}: {str(e)}")
        raise

def read_json_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Dict[str, Any]:
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
    try:
        file_path = Path(file_path)
        logger.debug(f"Reading JSON file: {file_path}")
        
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
            
        logger.debug(f"Successfully read JSON from {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in file {file_path}: {str(e)}")
        raise

def write_json_file(
    file_path: Union[str, Path], 
    data: Dict[str, Any], 
    encoding: str = 'utf-8', 
    create_dirs: bool = True, 
    indent: int = 2
) -> None:
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
    try:
        file_path = Path(file_path)
        logger.debug(f"Writing to JSON file: {file_path}")
        
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent)
            
        logger.debug(f"Successfully wrote JSON to {file_path}")
    except IOError as e:
        logger.error(f"Error writing JSON to file {file_path}: {str(e)}")
        raise

def read_csv_file(
    file_path: Union[str, Path], 
    encoding: str = 'utf-8', 
    delimiter: str = ',', 
    has_header: bool = True
) -> List[Dict[str, str]] if has_header else List[List[str]]:
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
    try:
        file_path = Path(file_path)
        logger.debug(f"Reading CSV file: {file_path}")
        
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
                data = list(reader)
            else:
                reader = csv.reader(f, delimiter=delimiter)
                data = list(reader)
            
        logger.debug(f"Successfully read {len(data)} rows from CSV file {file_path}")
        return data
    except FileNotFoundError:
        logger.error(f"CSV file not found: {file_path}")
        raise
    except csv.Error as e:
        logger.error(f"Error parsing CSV file {file_path}: {str(e)}")
        raise

def write_csv_file(
    file_path: Union[str, Path], 
    data: Union[List[Dict[str, Any]], List[List[Any]]], 
    headers: Optional[List[str]] = None,
    encoding: str = 'utf-8', 
    delimiter: str = ',', 
    create_dirs: bool = True
) -> None:
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
    try:
        file_path = Path(file_path)
        logger.debug(f"Writing to CSV file: {file_path}")
        
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding, newline='') as f:
            # Determine if we're working with a list of dicts or a list of lists
            if data and isinstance(data[0], dict):
                # Get headers from the first dict if not provided
                fieldnames = headers or list(data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            else:
                if not headers:
                    raise ValueError("Headers must be provided when data is a list of lists")
                writer = csv.writer(f, delimiter=delimiter)
                writer.writerow(headers)
                writer.writerows(data)
            
        logger.debug(f"Successfully wrote {len(data)} rows to CSV file {file_path}")
    except IOError as e:
        logger.error(f"Error writing to CSV file {file_path}: {str(e)}")
        raise

def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory
        
    Returns:
        Path object for the directory
        
    Raises:
        IOError: If the directory cannot be created
    """
    try:
        directory_path = Path(directory_path)
        logger.debug(f"Ensuring directory exists: {directory_path}")
        
        directory_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Directory exists: {directory_path}")
        return directory_path
    except IOError as e:
        logger.error(f"Error creating directory {directory_path}: {str(e)}")
        raise

def list_files(
    directory_path: Union[str, Path], 
    pattern: str = "*", 
    recursive: bool = False,
    include_dirs: bool = False
) -> List[Path]:
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
    try:
        directory_path = Path(directory_path)
        logger.debug(
            f"Listing files in {directory_path} with pattern {pattern}, "
            f"recursive={recursive}, include_dirs={include_dirs}"
        )
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if recursive:
            if include_dirs:
                files = list(directory_path.glob(f"**/{pattern}"))
            else:
                files = [f for f in directory_path.glob(f"**/{pattern}") if f.is_file()]
        else:
            if include_dirs:
                files = list(directory_path.glob(pattern))
            else:
                files = [f for f in directory_path.glob(pattern) if f.is_file()]
        
        logger.debug(f"Found {len(files)} matching files")
        return files
    except Exception as e:
        logger.error(f"Error listing files in {directory_path}: {str(e)}")
        raise

def copy_file(source_path: Union[str, Path], target_path: Union[str, Path], create_dirs: bool = True) -> None:
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
    try:
        source_path = Path(source_path)
        target_path = Path(target_path)
        logger.debug(f"Copying file from {source_path} to {target_path}")
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if create_dirs:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, target_path)
        
        logger.debug(f"Successfully copied file to {target_path}")
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error copying file: {str(e)}")
        raise

def move_file(source_path: Union[str, Path], target_path: Union[str, Path], create_dirs: bool = True) -> None:
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
    try:
        source_path = Path(source_path)
        target_path = Path(target_path)
        logger.debug(f"Moving file from {source_path} to {target_path}")
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if create_dirs:
            target_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(source_path, target_path)
        
        logger.debug(f"Successfully moved file to {target_path}")
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error moving file: {str(e)}")
        raise

def delete_file(file_path: Union[str, Path], ignore_missing: bool = False) -> bool:
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
    try:
        file_path = Path(file_path)
        logger.debug(f"Deleting file: {file_path}")
        
        if not file_path.exists():
            if ignore_missing:
                logger.debug(f"File does not exist, ignoring: {file_path}")
                return False
            else:
                raise FileNotFoundError(f"File not found: {file_path}")
        
        file_path.unlink()
        
        logger.debug(f"Successfully deleted file: {file_path}")
        return True
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        raise
