"""Tests for intent detection and prompt templates."""
import pytest
from app.agent.intent_detector import IntentDetector
from app.agent.prompt_templates import PromptTemplates
from app.config import settings

@pytest.fixture
def intent_detector():
    """Create an intent detector instance."""
    return IntentDetector()

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
                    "confidence": 0.8,
                    "entities": {
                        "participant": "John",
                        "time": "tomorrow at 2pm"
                    }
                }
            },
            {
                "input": "What meetings do I have today?",
                "expected": {
                    "intent": "list_events",
                    "confidence": 0.9,
                    "entities": {
                        "time": "today"
                    }
                }
            },
            {
                "input": "Cancel my 3pm meeting",
                "expected": {
                    "intent": "delete_event",
                    "confidence": 0.85,
                    "entities": {
                        "time": "3pm"
                    }
                }
            }
        ]

        for test_case in test_cases:
            result = intent_detector.detect(test_case["input"])
            assert result["intent"] == test_case["expected"]["intent"]
            assert result["confidence"] >= test_case["expected"]["confidence"]
            assert all(
                result["entities"].get(k) == v
                for k, v in test_case["expected"]["entities"].items()
            )

    def test_ambiguous_intent_detection(self, intent_detector):
        """Test intent detection for ambiguous phrases."""
        test_cases = [
            {
                "input": "Meeting with John",
                "expected_intents": ["create_event", "list_events"]
            },
            {
                "input": "Check my schedule",
                "expected_intents": ["list_events", "check_availability"]
            }
        ]

        for test_case in test_cases:
            result = intent_detector.detect(test_case["input"])
            assert result["intent"] in test_case["expected_intents"]
            assert result["confidence"] < 0.8  # Lower confidence for ambiguous cases

    def test_entity_extraction(self, intent_detector):
        """Test entity extraction from user input."""
        test_cases = [
            {
                "input": "Schedule a meeting with John and Sarah tomorrow at 2pm for 1 hour",
                "expected_entities": {
                    "participants": ["John", "Sarah"],
                    "time": "tomorrow at 2pm",
                    "duration": "1 hour"
                }
            },
            {
                "input": "Find a free slot between 9am and 5pm next Monday",
                "expected_entities": {
                    "start_time": "9am",
                    "end_time": "5pm",
                    "date": "next Monday"
                }
            }
        ]

        for test_case in test_cases:
            result = intent_detector.detect(test_case["input"])
            assert all(
                result["entities"].get(k) == v
                for k, v in test_case["expected_entities"].items()
            )

    def test_error_handling(self, intent_detector):
        """Test error handling for invalid inputs."""
        test_cases = [
            "",
            None,
            "   ",
            "!@#$%^&*()"
        ]

        for test_case in test_cases:
            with pytest.raises(ValueError):
                intent_detector.detect(test_case)

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
            "time": "tomorrow at 2pm",
            "duration": "1 hour"
        }

        result = prompt_templates.format_template(template, variables)
        assert "John" in result
        assert "tomorrow at 2pm" in result
        assert "1 hour" in result

    def test_missing_variables(self, prompt_templates):
        """Test handling of missing template variables."""
        template = prompt_templates.get_template("create_event")
        variables = {
            "participant": "John"
            # Missing time and duration
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
        
        assert template1 is template2  # Should be the same object

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