"""Prompt templates for the calendar assistant."""
from typing import Dict, Any
import string

class PromptTemplates:
    """Templates for various prompts used by the calendar assistant."""
    
    def __init__(self):
        """Initialize prompt templates."""
        self._templates = {
            "create_event": "Schedule a meeting with {participant} at {time} for {duration}",
            "list_events": "Show my calendar for {date}",
            "delete_event": "Cancel my meeting at {time} on {date}",
            "check_availability": "Find a free slot between {start_time} and {end_time} on {date}"
        }
        self._cache = {}
        
    def get_template(self, template_name: str) -> str:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            The template string
            
        Raises:
            ValueError: If template doesn't exist
        """
        if template_name not in self._templates:
            raise ValueError(f"Template '{template_name}' not found")
            
        # Return from cache if available
        if template_name in self._cache:
            return self._cache[template_name]
            
        template = self._templates[template_name]
        self._cache[template_name] = template
        return template
        
    def format_template(self, template: str, variables: Dict[str, str]) -> str:
        """
        Format a template with variables.
        
        Args:
            template: The template string
            variables: Dictionary of variables to substitute
            
        Returns:
            Formatted template string
            
        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing variables
        required_vars = set(string.Formatter().parse(template))
        missing_vars = [v[1] for v in required_vars if v[1] and v[1] not in variables]
        
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
            
        return template.format(**variables)
        
    def validate_template(self, template: str) -> bool:
        """
        Validate a template string.
        
        Args:
            template: The template string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            string.Formatter().parse(template)
            return True
        except ValueError:
            return False
            
    def update_template(self, template_name: str, new_template: str) -> None:
        """
        Update an existing template.
        
        Args:
            template_name: Name of the template to update
            new_template: New template string
            
        Raises:
            ValueError: If template doesn't exist or is invalid
        """
        if template_name not in self._templates:
            raise ValueError(f"Template '{template_name}' not found")
            
        if not self.validate_template(new_template):
            raise ValueError("Invalid template format")
            
        self._templates[template_name] = new_template
        # Clear cache for this template
        self._cache.pop(template_name, None)

    @staticmethod
    def get_intent_detection_prompt(text: str) -> str:
        """Get the prompt for intent detection."""
        return f"""
        Analyze the following user input and determine their intent:
        "{text}"
        
        Possible intents:
        - create_event: User wants to create a new calendar event
        - update_event: User wants to modify an existing event
        - delete_event: User wants to remove an event
        - list_events: User wants to see their upcoming events
        - find_free_slots: User wants to find available time slots
        - unknown: Intent cannot be determined
        
        Return the intent and any relevant entities in JSON format.
        """
    
    @staticmethod
    def get_event_creation_prompt(event_details: Dict) -> str:
        """Get the prompt for event creation."""
        return f"""
        Create a calendar event with the following details:
        Summary: {event_details.get('summary', 'Untitled Event')}
        Description: {event_details.get('description', '')}
        Start: {event_details.get('start_datetime', '')}
        End: {event_details.get('end_datetime', '')}
        Location: {event_details.get('location', '')}
        Attendees: {', '.join(event_details.get('attendees', []))}
        
        Please confirm these details and create the event.
        """
    
    @staticmethod
    def get_event_update_prompt(event_id: str, updates: Dict) -> str:
        """Get the prompt for event updates."""
        return f"""
        Update event {event_id} with the following changes:
        {updates}
        
        Please confirm these changes and update the event.
        """
    
    @staticmethod
    def get_event_deletion_prompt(event_id: str) -> str:
        """Get the prompt for event deletion."""
        return f"""
        Delete event {event_id}.
        Please confirm this action.
        """
    
    @staticmethod
    def get_event_listing_prompt(time_range: Dict) -> str:
        """Get the prompt for listing events."""
        return f"""
        List all events between {time_range.get('start', '')} and {time_range.get('end', '')}.
        """
    
    @staticmethod
    def get_free_slots_prompt(duration: int, time_range: Dict) -> str:
        """Get the prompt for finding free slots."""
        return f"""
        Find available {duration}-minute slots between {time_range.get('start', '')} and {time_range.get('end', '')}.
        """ 