# api/v1/schemas/files.py - Updated for Pydantic V2
"""
File API Schemas Module - Updated for Pydantic V2
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

class FileType(str, Enum):
    """File types supported for processing."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    XLSX = "xlsx"
    JPG = "jpg"
    PNG = "png"
    UNKNOWN = "unknown"

class FileMetadata(BaseModel):
    """Metadata about a processed file."""
    filename: str
    file_type: FileType
    size_bytes: int
    num_pages: Optional[int] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None

class FileContents(BaseModel):
    """Contents extracted from a file."""
    text: str
    metadata: FileMetadata
    tables: Optional[List[Dict]] = None
    images: Optional[List[str]] = None

class FileUploadRequest(BaseModel):
    """Schema for file upload request."""
    file: bytes = Field(..., description="File binary content")
    filename: str = Field(..., description="Original filename")
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename is not empty."""
        if not v.strip():
            raise ValueError("Filename cannot be empty")
        return v

class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    contents: FileContents

class FileProcessRequest(BaseModel):
    """Schema for file processing with LLM request."""
    file: bytes = Field(..., description="File binary content")
    filename: str = Field(..., description="Original filename")
    prompt_prefix: Optional[str] = Field(
        default="Summarize the following content:",
        description="Prefix to add before file content in prompt"
    )
    max_tokens: Optional[int] = Field(
        default=500,
        description="Maximum number of tokens to generate",
        gt=0
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Controls randomness in output (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Validate filename is not empty."""
        if not v.strip():
            raise ValueError("Filename cannot be empty")
        return v

class FileProcessResponse(BaseModel):
    """Schema for file processing with LLM response."""
    result: str = Field(..., description="LLM processing result")
    metadata: FileMetadata = Field(..., description="File metadata")