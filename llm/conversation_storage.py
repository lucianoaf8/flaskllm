# llm/conversation.py
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

class MessageRole(str, Enum):
    """Message role in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    """Message in a conversation."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Conversation(BaseModel):
    """Conversation with message history."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: Optional[str] = None
    system_prompt: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    metadata: Dict = Field(default_factory=dict)

    def add_message(self, role: MessageRole, content: str) -> Message:
        """
        Add a message to the conversation.

        Args:
            role: Message role
            content: Message content

        Returns:
            Added message
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from the conversation.

        Args:
            limit: Maximum number of messages to return (from most recent)

        Returns:
            List of messages
        """
        if limit is not None:
            return self.messages[-limit:]
        return self.messages

    def as_prompt_messages(self) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM prompt.

        Returns:
            List of message dictionaries
        """
        prompt_messages = []

        # Add system prompt if available
        if self.system_prompt:
            prompt_messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # Add conversation messages
        for message in self.messages:
            prompt_messages.append({
                "role": message.role,
                "content": message.content
            })

        return prompt_messages
