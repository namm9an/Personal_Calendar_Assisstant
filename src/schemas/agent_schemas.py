from typing import Dict, Any, Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class AgentRequest(BaseModel):
    """Request schema for the calendar agent endpoint."""
    text: str = Field(..., description="User's natural language command")
    provider: Literal["google", "microsoft"] = Field(..., description="Calendar provider to use")

class AgentStep(BaseModel):
    """Schema for each step in the agent's reasoning process."""
    step_number: int = Field(..., description="Step number in the sequence")
    message: str = Field(..., description="Explanation or intermediate reasoning")
    tool_invoked: Optional[str] = Field(None, description="Name of the tool that was invoked")
    tool_input: Optional[Dict[str, Any]] = Field(None, description="Input passed to the tool")
    tool_output: Optional[Dict[str, Any]] = Field(None, description="Output from the tool")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this step occurred")

class AgentResponse(BaseModel):
    """Final response schema for the calendar agent endpoint."""
    final_intent: str = Field(..., description="The detected intent (list_events, find_free_slots, etc.)")
    final_output: Dict[str, Any] = Field(..., description="The final output from the agent")
    summary: str = Field(..., description="Human-friendly summary of what happened")
    steps: List[AgentStep] = Field(default_factory=list, description="Sequence of steps taken")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the response was generated")

class AgentError(BaseModel):
    """Error response schema for the calendar agent endpoint."""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred") 