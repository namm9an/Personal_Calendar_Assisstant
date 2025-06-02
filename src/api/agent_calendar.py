import os
import json
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..schemas.agent_schemas import AgentRequest, AgentResponse, AgentStep, AgentError
from ..agents.llm_selector import LLMSelector
from ..core.auth import get_current_user
from ..core.exceptions import ToolExecutionError

router = APIRouter(prefix="/api/v1/agent")

# Initialize LLM selector
llm_selector = LLMSelector()

def detect_intent(text: str) -> str:
    """Detect the intent from the user's text.
    
    This is a simple keyword-based implementation. In a real system, you might:
    1. Use a small classification model
    2. Use embeddings and similarity search
    3. Use a more sophisticated NLP pipeline
    """
    text = text.lower()
    
    if any(word in text for word in ["show", "list", "what", "when", "events", "calendar"]):
        return "list_events"
    elif any(word in text for word in ["free", "available", "slot", "time"]):
        return "find_free_slots"
    elif any(word in text for word in ["schedule", "create", "add", "book", "meeting"]):
        return "create_event"
    elif any(word in text for word in ["move", "reschedule", "change", "update"]):
        return "reschedule_event"
    elif any(word in text for word in ["cancel", "delete", "remove"]):
        return "cancel_event"
    else:
        return "unknown"

def load_prompt_template(intent: str, user_text: str) -> str:
    """Load and format the appropriate prompt template."""
    template_path = os.path.join("src", "agents", "prompts", f"{intent}_prompt.txt")
    
    try:
        with open(template_path, "r") as f:
            template = f.read()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"Prompt template not found for intent: {intent}"
        )
    
    return template.format(user_input=user_text)

async def run_langgraph(
    user_id: str,
    provider: str,
    prompt: str,
    llm_selector: LLMSelector
) -> AsyncGenerator[Dict[str, Any], None]:
    """Run the LangGraph with the given prompt and context.
    
    This is a placeholder implementation. In a real system, you would:
    1. Load the LangGraph from a file
    2. Set up the graph with the correct tools
    3. Run the graph with the prompt and context
    4. Stream back the results
    """
    # For now, just yield a simple sequence of steps
    yield {
        "message": "Analyzing your request...",
        "tool": None,
        "input": None,
        "output": None
    }
    
    # Simulate tool execution
    try:
        # Get LLM response
        llm_response = await llm_selector.generate_with_fallback(
            user_id=user_id,
            prompt=prompt,
            is_json=True
        )
        
        yield {
            "message": "Processing your request...",
            "tool": "calendar_tool",
            "input": llm_response,
            "output": {"status": "success"}
        }
        
        # Final step
        yield {
            "message": "Request completed successfully",
            "tool": None,
            "input": None,
            "output": None
        }
    except Exception as e:
        yield {
            "message": f"Error: {str(e)}",
            "tool": None,
            "input": None,
            "output": None
        }

@router.post("/calendar")
async def run_calendar_agent(
    request: Request,
    payload: AgentRequest,
    user = Depends(get_current_user)
) -> StreamingResponse:
    """Run the calendar agent with the given prompt."""
    try:
        # 1. Detect intent
        intent = detect_intent(payload.text)
        if intent == "unknown":
            raise HTTPException(
                status_code=400,
                detail="Could not recognize intent from input"
            )
        
        # 2. Load prompt template
        prompt = load_prompt_template(intent, payload.text)
        
        # 3. Run LangGraph
        async def event_generator():
            step_number = 0
            steps = []
            final_output = None
            
            async for node_event in run_langgraph(
                user_id=str(user.id),
                provider=payload.provider,
                prompt=prompt,
                llm_selector=llm_selector
            ):
                step_number += 1
                step = AgentStep(
                    step_number=step_number,
                    message=node_event["message"],
                    tool_invoked=node_event.get("tool"),
                    tool_input=node_event.get("input"),
                    tool_output=node_event.get("output")
                )
                steps.append(step)
                
                # If this is the last step, save the output
                if node_event.get("output"):
                    final_output = node_event["output"]
                
                yield f"data: {step.json()}\n\n"
            
            # After stream ends, send final response
            response = AgentResponse(
                final_intent=intent,
                final_output=final_output or {},
                summary=f"Successfully processed {intent} request",
                steps=steps
            )
            yield f"data: {response.json()}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        error = AgentError(
            error=str(e),
            details={"intent": intent} if "intent" in locals() else None
        )
        return StreamingResponse(
            iter([f"data: {error.json()}\n\n"]),
            media_type="text/event-stream"
        ) 