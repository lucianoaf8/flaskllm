# llm/storage/conversations.py
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from core.exceptions import APIError
from core.logging import get_logger

# Configure logger
logger = get_logger(__name__)

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


class ConversationStorage:
    """Storage for conversations."""

    def __init__(self, db_client=None):
        """
        Initialize conversation storage.

        Args:
            db_client: Database client (if None, uses in-memory storage)
        """
        self.db_client = db_client
        self.conversations: Dict[str, Conversation] = {}
        logger.info("Conversation storage initialized")

    def create_conversation(self, user_id: str, system_prompt: Optional[str] = None, title: Optional[str] = None) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID
            system_prompt: System prompt for the conversation
            title: Conversation title

        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            system_prompt=system_prompt,
            title=title
        )

        # Store the conversation
        self.conversations[conversation.id] = conversation
        logger.info(
            "Created new conversation",
            conversation_id=conversation.id,
            user_id=user_id
        )

        return conversation

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation or None if not found
        """
        return self.conversations.get(conversation_id)

    def update_conversation(self, conversation: Conversation) -> None:
        """
        Update a conversation.

        Args:
            conversation: Conversation to update
        """
        conversation.updated_at = datetime.utcnow()
        self.conversations[conversation.id] = conversation
        logger.info(
            "Updated conversation",
            conversation_id=conversation.id,
            user_id=conversation.user_id
        )

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(
                "Deleted conversation",
                conversation_id=conversation_id
            )
            return True
        return False

    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """
        Get all conversations for a user.

        Args:
            user_id: User ID

        Returns:
            List of conversations
        """
        return [
            conversation for conversation in self.conversations.values()
            if conversation.user_id == user_id
        ]
