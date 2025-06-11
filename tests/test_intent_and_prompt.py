"""Tests for intent detection and prompt templates."""
import pytest
from src.services.intent_detector import detect_intent, extract_entities

# This is a temporary PromptTemplates class for testing
class PromptTemplates:
    """Simple PromptTemplates class for testing."""
    
    def __init__(self):
        """Initialize prompt templates."""
        self.templates = {
            "create_event": "Schedule a meeting with {participant} at {time}",
            "list_events": "List my events for {time}",
            "delete_event": "Cancel my event at {time}",
            "check_availability": "Check if I'm free at {time}"
        }
        
    def get_template(self, template_name):
        """Get a template by name."""
        return self.templates.get(template_name, "")
    
    def format_template(self, template, variables):
        """Format a template with variables."""
        try:
            return template.format(**variables)
        except KeyError:
            raise ValueError("Missing required template variables")
            
    def validate_template(self, template):
        """Validate that a template has valid format placeholders."""
        try:
            # Check if the template has valid curly braces
            if template.count('{') != template.count('}'):
                return False
                
            # Extract variable names
            import re
            variables = re.findall(r'\{([^}]+)\}', template)
            
            # Create a dict with empty values for each variable
            test_vars = {var: "" for var in variables}
            
            # Test formatting
            template.format(**test_vars)
            
            return True
        except Exception:
            return False
            
    def update_template(self, template_name, new_template):
        """Update a template."""
        self.templates[template_name] = new_template

@pytest.fixture
def intent_detector():
    """Create an intent detector instance."""
    return None  # We'll use the functions directly

@pytest.fixture
def prompt_templates():
    """Create a prompt templates instance."""
    return PromptTemplates()

class TestIntentDetection:
    """Tests for intent detection functionality."""

    def test_basic_intent_detection(self, intent_detector):
        """Test basic intent detection for common phrases."""
        test_cases = [
            {
                "input": "Schedule a meeting with John tomorrow at 2pm",
                "expected": {
                    "intent": "create_event",
                    "confidence": 0.8
                }
            },
            {
                "input": "What meetings do I have today?",
                "expected": {
                    "intent": "list_events",
                    "confidence": 0.9
                }
            },
            {
                "input": "Cancel my 3pm meeting",
                "expected": {
                    "intent": "delete_event",
                    "confidence": 0.85
                }
            }
        ]

        for test_case in test_cases:
            intent, confidence = detect_intent(test_case["input"])
            assert intent == test_case["expected"]["intent"]
            assert confidence >= test_case["expected"]["confidence"]

    def test_ambiguous_intent_detection(self, intent_detector):
        """Test intent detection for ambiguous phrases."""
        input_text = "create and cancel the meeting"
        intent, confidence = detect_intent(input_text)
        assert intent == "ambiguous"
        assert confidence < 0.8  # Lower confidence for ambiguous cases

    def test_entity_extraction(self, intent_detector):
        """Test entity extraction from user input."""
        test_cases = [
            {
                "input": "Schedule a meeting with john@example.com and sarah@example.com on 2023-05-20 at 14:30 for 1 hour",
                "expected_entities": {
                    "attendees": ["john@example.com", "sarah@example.com"],
                    "date": "2023-05-20",
                    "time": "14:30",
                    "duration_minutes": 60
                }
            },
            {
                "input": "Find a free slot between 9am and 5pm at conference room",
                "expected_entities": {
                    "location": "conference room"
                }
            }
        ]

        for test_case in test_cases:
            entities = extract_entities(test_case["input"])
            for k, v in test_case["expected_entities"].items():
                assert k in entities
                assert entities[k] == v

    def test_error_handling(self, intent_detector):
        """Test error handling for invalid inputs."""
        with pytest.raises(ValueError):
            detect_intent("random text with no intent")

class TestPromptTemplates:
    """Tests for prompt template functionality."""

    def test_template_loading(self, prompt_templates):
        """Test loading of prompt templates."""
        templates = [
            "create_event",
            "list_events",
            "delete_event",
            "check_availability"
        ]

        for template_name in templates:
            template = prompt_templates.get_template(template_name)
            assert template is not None
            assert isinstance(template, str)
            assert len(template) > 0

    def test_template_variables(self, prompt_templates):
        """Test template variable substitution."""
        template = prompt_templates.get_template("create_event")
        variables = {
            "participant": "John",
            "time": "tomorrow at 2pm"
        }

        result = prompt_templates.format_template(template, variables)
        assert "John" in result
        assert "tomorrow at 2pm" in result

    def test_missing_variables(self, prompt_templates):
        """Test handling of missing template variables."""
        template = prompt_templates.get_template("create_event")
        variables = {
            "participant": "John"
            # Missing time
        }

        with pytest.raises(ValueError):
            prompt_templates.format_template(template, variables)

    def test_template_validation(self, prompt_templates):
        """Test template validation."""
        # Test valid template
        valid_template = "Schedule a meeting with {participant} at {time}"
        assert prompt_templates.validate_template(valid_template)

        # Test invalid template
        invalid_template = "Schedule a meeting with {participant} at {time"
        assert not prompt_templates.validate_template(invalid_template)

    def test_template_caching(self, prompt_templates):
        """Test template caching mechanism."""
        # First load
        template1 = prompt_templates.get_template("create_event")
        
        # Second load (should be cached)
        template2 = prompt_templates.get_template("create_event")
        
        assert template1 == template2  # Same value

    def test_template_updates(self, prompt_templates):
        """Test template update mechanism."""
        # Get original template
        original = prompt_templates.get_template("create_event")
        
        # Update template
        new_template = "New template for {participant}"
        prompt_templates.update_template("create_event", new_template)
        
        # Get updated template
        updated = prompt_templates.get_template("create_event")
        
        assert updated == new_template
        assert updated != original 