import pytest
from src.services.intent_detector import detect_intent, extract_entities

def test_detect_intent_create():
    """Test detecting create event intent."""
    intent, confidence = detect_intent("create a meeting tomorrow")
    assert intent == "create_event"
    assert confidence > 0.8

def test_detect_intent_list():
    """Test detecting list events intent."""
    intent, confidence = detect_intent("show my meetings")
    assert intent == "list_events"
    assert confidence > 0.8

def test_detect_intent_find_slots():
    """Test detecting find free slots intent."""
    intent, confidence = detect_intent("find free time tomorrow")
    assert intent == "find_free_slots"
    assert confidence > 0.8

def test_detect_intent_update():
    """Test detecting update event intent."""
    intent, confidence = detect_intent("change my meeting time")
    assert intent == "update_event"
    assert confidence > 0.8

def test_detect_intent_delete():
    """Test detecting delete event intent."""
    intent, confidence = detect_intent("remove my meeting")
    assert intent == "delete_event"
    assert confidence > 0.8

def test_detect_intent_reschedule():
    """Test detecting reschedule event intent."""
    intent, confidence = detect_intent("move my meeting to next week")
    assert intent == "reschedule_event"
    assert confidence > 0.8

def test_detect_intent_ambiguous():
    """Test detecting ambiguous intent."""
    intent, confidence = detect_intent("create and cancel the meeting tomorrow")
    assert intent == "ambiguous"
    assert confidence < 0.6

def test_detect_intent_unknown():
    """Test detecting unknown intent."""
    with pytest.raises(ValueError):
        detect_intent("random text")

def test_extract_entities_date():
    """Test extracting date entity."""
    entities = extract_entities("meeting on 2024-03-20")
    assert "date" in entities
    assert entities["date"] == "2024-03-20"

def test_extract_entities_time():
    """Test extracting time entity."""
    entities = extract_entities("meeting at 14:30")
    assert "time" in entities
    assert entities["time"] == "14:30"

def test_extract_entities_duration():
    """Test extracting duration entity."""
    entities = extract_entities("1 hour meeting")
    assert "duration_minutes" in entities
    assert entities["duration_minutes"] == 60

def test_extract_entities_attendees():
    """Test extracting attendees entity."""
    entities = extract_entities("meeting with john@example.com and jane@example.com")
    assert "attendees" in entities
    assert len(entities["attendees"]) == 2
    assert "john@example.com" in entities["attendees"]
    assert "jane@example.com" in entities["attendees"]

def test_extract_entities_location():
    """Test extracting location entity."""
    entities = extract_entities("meeting at conference room")
    assert "location" in entities
    assert entities["location"] == "conference room" 