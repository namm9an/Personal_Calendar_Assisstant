from typing import Tuple, Dict, Any
import re
from datetime import datetime

def detect_intent(text: str) -> Tuple[str, float]:
    """Detect intent from user input."""
    text_lower = text.lower()
    
    # Basic intent detection rules
    if any(word in text_lower for word in ["create", "schedule", "book", "add"]):
        if "meeting" in text_lower or "event" in text_lower:
            return "create_event", 0.95
        elif "slot" in text_lower or "time" in text_lower:
            return "find_free_slots", 0.90
    
    elif any(word in text_lower for word in ["update", "change", "modify"]):
        if "meeting" in text_lower or "event" in text_lower:
            return "update_event", 0.95
    
    elif any(word in text_lower for word in ["delete", "remove", "cancel"]):
        if "meeting" in text_lower or "event" in text_lower:
            return "delete_event", 0.95
    
    elif any(word in text_lower for word in ["reschedule", "move"]):
        if "meeting" in text_lower or "event" in text_lower:
            return "reschedule_event", 0.95
    
    elif any(word in text_lower for word in ["list", "show", "get"]):
        if "meeting" in text_lower or "event" in text_lower:
            return "list_events", 0.90
    
    # Ambiguous cases
    if any(word in text_lower for word in ["create", "schedule"]) and any(word in text_lower for word in ["cancel", "delete"]):
        return "ambiguous", 0.5
    
    # No intent detected
    raise ValueError("Could not detect intent from input")

def extract_entities(text: str) -> Dict[str, Any]:
    """Extract entities from user input."""
    entities = {}
    
    # Extract date
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    date_match = re.search(date_pattern, text)
    if date_match:
        entities["date"] = date_match.group(0)
    
    # Extract time
    time_pattern = r"\d{2}:\d{2}"
    time_match = re.search(time_pattern, text)
    if time_match:
        entities["time"] = time_match.group(0)
    
    # Extract duration
    duration_pattern = r"(\d+)\s*(?:hour|hr|h|minute|min|m)s?"
    duration_match = re.search(duration_pattern, text.lower())
    if duration_match:
        value = int(duration_match.group(1))
        unit = duration_match.group(0).lower()
        if "hour" in unit or "hr" in unit or "h" in unit:
            entities["duration_minutes"] = value * 60
        else:
            entities["duration_minutes"] = value
    
    # Extract attendees
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(email_pattern, text)
    if emails:
        entities["attendees"] = emails
    
    # Extract location
    location_pattern = r"at\s+([^,.]+)"
    location_match = re.search(location_pattern, text.lower())
    if location_match:
        entities["location"] = location_match.group(1).strip()
    
    return entities 