"""
LangGraph agent for the Personal Calendar Assistant.
"""
import json
import logging
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, Sequence, TypedDict
import os

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.output_parsers.openai_functions import (
    OpenAIFunctionsAgentOutputParser,
)
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.schema.runnable import (
    Runnable,
    RunnableConfig,
    RunnablePassthrough,
)
from langchain.tools import BaseTool
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy.orm import Session

from app.agent.prompts import (
    ATTENDEE_EXTRACTION_PROMPT,
    CALENDAR_ASSISTANT_PROMPT,
    EVENT_EXTRACTION_PROMPT,
    TIME_EXTRACTION_PROMPT,
)
from app.agent.tools import CalendarTools
from app.models.user import User
from app.services.google_calendar import GoogleCalendarService

logger = logging.getLogger(__name__)

# Replace hardcoded keys with environment variables
CHAT_HISTORY_KEY = os.getenv("CHAT_HISTORY_KEY", "chat_history")
INPUT_KEY = os.getenv("INPUT_KEY", "input")

class AgentState(TypedDict):
    """State for the agent graph."""
    
    # Messages in the conversation
    messages: List[BaseMessage]
    
    # Current user input being processed
    input: Optional[str]
    
    # Extracted date/time information
    time_info: Optional[Dict[str, Any]]
    
    # Extracted attendee information
    attendee_info: Optional[Dict[str, Any]]
    
    # Extracted event details
    event_info: Optional[Dict[str, Any]]
    
    # Current agent actions/thoughts
    agent_scratchpad: List[BaseMessage]
    
    # Whether we need more information from the user
    needs_more_info: bool


def initialize_agent(user: User, db: Session, gemini_api_key: str):
    """
    Initialize the LangGraph agent for calendar operations.
    
    Args:
        user: User for whom the agent is processing requests
        db: Database session
        gemini_api_key: API key for Gemini Pro
        
    Returns:
        StateGraph: The agent graph
    """
    # Initialize tools
    calendar_tools = CalendarTools(user, db)
    tools = calendar_tools.get_tools()
    
    # Initialize memory
    memory = ConversationBufferMemory(
        return_messages=True,
        memory_key=CHAT_HISTORY_KEY,
        input_key=INPUT_KEY,
    )
    
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0.1,
        model="gpt-4-turbo-preview",  # Would be replaced with Gemini Pro once native LangChain support is stable
        api_key=gemini_api_key,
    )
    
    # Add user's working hours and timezone to the prompt
    working_hours_start = user.working_hours_start.strftime("%H:%M")
    working_hours_end = user.working_hours_end.strftime("%H:%M")
    timezone = user.timezone
    
    # Create prompt template with user's working hours and timezone
    prompt = CALENDAR_ASSISTANT_PROMPT.partial(
        working_hours_start=working_hours_start,
        working_hours_end=working_hours_end,
        timezone=timezone,
    )
    
    # Initialize the agent
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)
    
    # Define state nodes
    
    # 1. Extract time information if needed
    def should_extract_time(state: AgentState) -> str:
        """
        Determine if we need to extract time information from the input.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to call
        """
        input_text = state["input"]
        
        # Skip if we already have time info or if this is a simple listing request
        if state["time_info"] or "list" in input_text.lower() or "show" in input_text.lower():
            return "agent"
            
        # Check if the input likely contains time-related information
        time_indicators = [
            "today", "tomorrow", "yesterday", "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday", "morning", "afternoon",
            "evening", "night", "hour", "minute", "am", "pm", "o'clock", "at",
            "from", "until", ":" 
        ]
        
        if any(indicator in input_text.lower() for indicator in time_indicators):
            return "extract_time"
            
        return "agent"
    
    def extract_time(state: AgentState) -> AgentState:
        """
        Extract time information from the input.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        input_text = state["input"]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Create time extraction prompt
        time_prompt = TIME_EXTRACTION_PROMPT.format(
            text=input_text,
            current_time=current_time,
            timezone=user.timezone,
        )
        
        # Call LLM to extract time information
        time_response = llm.invoke(time_prompt)
        
        try:
            # Extract JSON from response
            time_info = json.loads(time_response.content)
            
            # Update state
            state["time_info"] = time_info
            
            return state
        except Exception as e:
            logger.error(f"Error extracting time information: {str(e)}")
            # If extraction fails, proceed without it
            state["time_info"] = {}
            return state
    
    # 2. Extract attendee information if needed
    def should_extract_attendees(state: AgentState) -> str:
        """
        Determine if we need to extract attendee information from the input.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to call
        """
        input_text = state["input"]
        
        # Skip if we already have attendee info or if this is a simple listing request
        if state["attendee_info"] or "list" in input_text.lower() or "show" in input_text.lower():
            return "agent"
            
        # Check if the input likely contains attendee-related information
        attendee_indicators = [
            "with", "invite", "attendee", "people", "person", "meet", "meeting",
            "@", "email", "invitees", "participant"
        ]
        
        if any(indicator in input_text.lower() for indicator in attendee_indicators):
            return "extract_attendees"
            
        return "agent"
    
    def extract_attendees(state: AgentState) -> AgentState:
        """
        Extract attendee information from the input.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        input_text = state["input"]
        
        # Create attendee extraction prompt
        attendee_prompt = ATTENDEE_EXTRACTION_PROMPT.format(text=input_text)
        
        # Call LLM to extract attendee information
        attendee_response = llm.invoke(attendee_prompt)
        
        try:
            # Extract JSON from response
            attendee_info = json.loads(attendee_response.content)
            
            # Update state
            state["attendee_info"] = attendee_info
            
            return state
        except Exception as e:
            logger.error(f"Error extracting attendee information: {str(e)}")
            # If extraction fails, proceed without it
            state["attendee_info"] = {"attendees": []}
            return state
    
    # 3. Extract event details if needed
    def should_extract_event_details(state: AgentState) -> str:
        """
        Determine if we need to extract event details from the input.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to call
        """
        input_text = state["input"].lower()
        
        # Skip if we already have event info or if this is a simple listing request
        if state["event_info"] or "list" in input_text or "show" in input_text:
            return "agent"
            
        # Check if the input likely contains event creation or modification
        event_indicators = [
            "schedule", "create", "book", "set up", "plan", "organize",
            "arrange", "add", "new", "meeting", "appointment", "call", 
            "update", "change", "modify", "reschedule", "move", "edit"
        ]
        
        if any(indicator in input_text for indicator in event_indicators):
            return "extract_event_details"
            
        return "agent"
    
    def extract_event_details(state: AgentState) -> AgentState:
        """
        Extract event details from the input.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        input_text = state["input"]
        
        # Create event details extraction prompt
        event_prompt = EVENT_EXTRACTION_PROMPT.format(text=input_text)
        
        # Call LLM to extract event details
        event_response = llm.invoke(event_prompt)
        
        try:
            # Extract JSON from response
            event_info = json.loads(event_response.content)
            
            # Update state
            state["event_info"] = event_info
            
            return state
        except Exception as e:
            logger.error(f"Error extracting event details: {str(e)}")
            # If extraction fails, proceed without it
            state["event_info"] = {}
            return state
    
    # 4. Agent node to process the input and generate a response
    def agent_node(state: AgentState) -> AgentState:
        """
        Process the input with the agent and generate a response.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        # Create agent inputs
        agent_inputs = {
            "input": state["input"],
            "chat_history": state.get("messages", []),
            "agent_scratchpad": state.get("agent_scratchpad", []),
        }
        
        # Add extracted information to the input
        if state.get("time_info"):
            agent_inputs["input"] += f"\n\nExtracted time information: {json.dumps(state['time_info'])}"
            
        if state.get("attendee_info"):
            agent_inputs["input"] += f"\n\nExtracted attendee information: {json.dumps(state['attendee_info'])}"
            
        if state.get("event_info"):
            agent_inputs["input"] += f"\n\nExtracted event details: {json.dumps(state['event_info'])}"
        
        # Run the agent
        agent_result = agent_executor.invoke(agent_inputs)
        
        # Update the state with the agent's response
        state["messages"].append(HumanMessage(content=state["input"]))
        state["messages"].append(AIMessage(content=agent_result["output"]))
        
        # Check if the agent needs more information
        needs_more = "need more information" in agent_result["output"].lower() or \
                    "need additional information" in agent_result["output"].lower() or \
                    "please provide" in agent_result["output"].lower() or \
                    "could you clarify" in agent_result["output"].lower()
                    
        state["needs_more_info"] = needs_more
        
        # Clear temporary state
        state["time_info"] = None
        state["attendee_info"] = None
        state["event_info"] = None
        state["agent_scratchpad"] = []
        
        return state
    
    # 5. Check if we need more information from the user
    def need_more_info(state: AgentState) -> str:
        """
        Determine if we need more information from the user.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to call
        """
        if state["needs_more_info"]:
            return END
        else:
            return END
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("check_time", should_extract_time)
    workflow.add_node("extract_time", extract_time)
    workflow.add_node("check_attendees", should_extract_attendees)
    workflow.add_node("extract_attendees", extract_attendees)
    workflow.add_node("check_event_details", should_extract_event_details)
    workflow.add_node("extract_event_details", extract_event_details)
    workflow.add_node("agent", agent_node)
    workflow.add_node("check_need_more", need_more_info)
    
    # Add edges
    workflow.set_entry_point("check_time")
    workflow.add_edge("check_time", "extract_time")
    workflow.add_edge("check_time", "check_attendees")
    workflow.add_edge("extract_time", "check_attendees")
    workflow.add_edge("check_attendees", "extract_attendees")
    workflow.add_edge("check_attendees", "check_event_details")
    workflow.add_edge("extract_attendees", "check_event_details")
    workflow.add_edge("check_event_details", "extract_event_details")
    workflow.add_edge("check_event_details", "agent")
    workflow.add_edge("extract_event_details", "agent")
    workflow.add_edge("agent", "check_need_more")
    workflow.add_edge("check_need_more", END)
    
    # Compile the graph
    compiled_graph = workflow.compile()
    
    return compiled_graph


class CalendarAssistantAgent:
    """Calendar Assistant Agent powered by LangGraph."""
    
    def __init__(self, user: User, db: Session, gemini_api_key: str):
        """
        Initialize the Calendar Assistant Agent.
        
        Args:
            user: User for whom the agent is processing requests
            db: Database session
            gemini_api_key: API key for Gemini Pro
        """
        self.user = user
        self.db = db
        self.graph = initialize_agent(user, db, gemini_api_key)
        self.state = {
            "messages": [],
            "input": None,
            "time_info": None,
            "attendee_info": None,
            "event_info": None,
            "agent_scratchpad": [],
            "needs_more_info": False,
        }
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate a response.
        
        Args:
            user_input: Natural language input from the user
            
        Returns:
            Agent response
        """
        # Update state with new input
        self.state["input"] = user_input
        
        # Process input through the graph
        result = self.graph.invoke(self.state)
        
        # Update state
        self.state = result
        
        # Return the latest response
        if self.state["messages"]:
            return self.state["messages"][-1].content
        else:
            return "I'm sorry, I couldn't process your request."
