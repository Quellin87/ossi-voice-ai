"""
Pydantic models for LLM responses and data structures.

These models ensure type-safe, validated responses from Claude.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class IntentType(str, Enum):
    """Valid intent types."""
    RECEPTIONIST = "receptionist"
    TRIAGE = "triage"
    ESCALATION = "escalation"


class IntentClassification(BaseModel):
    """
    Structured output for intent classification.
    
    This forces Claude to return a valid, type-checked response.
    """
    intent: IntentType = Field(
        description="The classified intent: receptionist, triage, or escalation"
    )
    confidence: float = Field(
        ge=0.0, 
        le=1.0,
        description="Confidence score from 0.0 to 1.0"
    )
    reasoning: str = Field(
        description="Brief explanation of the classification decision"
    )
    next_action: str = Field(
        description="What should happen next in the conversation"
    )
    detected_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords that influenced the decision"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "receptionist",
                "confidence": 0.95,
                "reasoning": "User is requesting appointment scheduling",
                "next_action": "Ask for preferred provider or specialty",
                "detected_keywords": ["appointment", "book", "schedule"]
            }
        }


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None


class ConversationContext(BaseModel):
    """
    Full conversation context.
    
    This is stored in Redis during active calls.
    """
    call_id: str
    user_id: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    current_intent: Optional[IntentType] = None
    conversation_turns: List[ConversationTurn] = Field(default_factory=list)
    patient_context: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    
    def add_turn(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add a conversation turn."""
        self.conversation_turns.append(
            ConversationTurn(role=role, content=content, metadata=metadata)
        )
    
    def get_recent_turns(self, n: int = 5) -> List[ConversationTurn]:
        """Get the last N conversation turns."""
        return self.conversation_turns[-n:] if self.conversation_turns else []


class LLMResponse(BaseModel):
    """Generic LLM response."""
    content: str
    tokens_used: int
    model: str
    latency_ms: float
    metadata: Optional[dict] = None
