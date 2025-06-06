"""Intent detection for calendar assistant."""
from typing import Dict, Any, List
import re

class IntentDetector:
    """Detects user intent from natural language input."""
    
    def __init__(self):
        """Initialize the intent detector."""
        self.intent_patterns = {
            "create_event": [
                r"schedule.*meeting",
                r"create.*event",
                r"add.*calendar",
                r"book.*meeting"
            ],
            "list_events": [
                r"what.*meetings",
                r"show.*calendar",
                r"list.*events",
                r"check.*schedule"
            ],
            "delete_event": [
                r"cancel.*meeting",
                r"delete.*event",
                r"remove.*calendar"
            ],
            "check_availability": [
                r"find.*free",
                r"check.*availability",
                r"when.*available"
            ]
        }
        
        self.entity_patterns = {
            "participant": r"with\s+(\w+)",
            "time": r"at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            "duration": r"for\s+(\d+\s*(?:hour|minute|day)s?)",
            "date": r"(?:on|for)\s+(\w+\s+\d{1,2}|\w+)"
        }

    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect intent and extract entities from text.
        
        Args:
            text: The input text to analyze
            
        Returns:
            Dict containing intent, confidence, and entities
            
        Raises:
            ValueError: If text is empty or invalid
        """
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("Invalid input text")
            
        text = text.lower().strip()
        
        # Find matching intent
        matched_intent = None
        confidence = 0.0
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    matched_intent = intent
                    confidence = 0.9  # High confidence for exact matches
                    break
            if matched_intent:
                break
                
        if not matched_intent:
            # Default to list_events for ambiguous cases
            matched_intent = "list_events"
            confidence = 0.5
            
        # Extract entities
        entities = {}
        for entity_type, pattern in self.entity_patterns.items():
            match = re.search(pattern, text)
            if match:
                entities[entity_type] = match.group(1)
                
        return {
            "intent": matched_intent,
            "confidence": confidence,
            "entities": entities
        } 