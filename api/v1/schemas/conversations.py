# api/v1/schemas/conversations.py - Updated for Pydantic V2
"""
Conversation Schema Definitions - Updated for Pydantic V2
"""
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator

class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

class Message(BaseModel):
    """Schema for a message in a conversation."""
    id: str = Field(..., description="Message ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class ConversationSummary(BaseModel):
    """Schema for a conversation summary."""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    title: Optional[str] = Field(default=None, description="Conversation title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(..., description="Number of messages")
    last_message: Optional[str] = Field(default=None, description="Last message content preview")

class Conversation(BaseModel):
    """Schema for a conversation."""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    title: Optional[str] = Field(default=None, description="Conversation title")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    messages: List[Message] = Field(default_factory=list, description="Conversation messages")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class ConversationRequest(BaseModel):
    """Schema for conversation creation request."""
    title: Optional[str] = Field(default=None, description="Conversation title")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    conversation: Union[Conversation, ConversationSummary] = Field(..., description="Conversation data")

class MessageRequest(BaseModel):
    """Schema for message creation request."""
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content is not empty."""
        if not v.strip():
            raise ValueError("Message content cannot be empty")
        return v

class MessageResponse(BaseModel):
    """Schema for message response."""
    message: Message = Field(..., description="Message data")