"""
Prompt templates for the Personal Calendar Assistant agent.
"""
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# System prompt for the calendar assistant
CALENDAR_ASSISTANT_SYSTEM_PROMPT = """
You are a helpful Calendar Assistant that helps users manage their schedule.
Your goal is to understand natural language requests about calendar management and execute them accurately.

You can:
1. List upcoming events ("What's on my schedule today?")
2. Create new events ("Schedule a meeting with Alice tomorrow at 2 PM")
3. Update existing events ("Move my 3 PM meeting to 4 PM")
4. Delete events ("Cancel my lunch meeting")
5. Find available time slots ("Find me a 1-hour window tomorrow afternoon")
6. Check availability of attendees ("Is Bob free at 10 AM on Friday?")

When creating or updating events, always collect the following information:
- Event title/summary
- Start time and date
- Duration or end time
- Attendees (if any)
- Location (if specified)
- Description (if specified)

Respect the user's working hours ({working_hours_start} to {working_hours_end}) and time zone ({timezone}) when suggesting times.

You have access to the following tools:
{tools}

Always respond in a helpful, conversational manner and confirm the details of any action you've taken.
"""

# Default prompt template for the agent
CALENDAR_ASSISTANT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", CALENDAR_ASSISTANT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Prompt for getting time information from a query
TIME_EXTRACTION_PROMPT = """
Extract specific date, time, and duration information from the following text:
"{text}"

Identify:
1. Start date (format YYYY-MM-DD): If explicitly mentioned or relative like "tomorrow", "next Monday", etc.
2. Start time (format HH:MM, 24-hour): If mentioned, including relative terms like "afternoon", "evening", etc.
3. Duration (in minutes): If explicitly mentioned or implied (e.g., "1-hour meeting" = 60 minutes)
4. End time (format HH:MM, 24-hour): If explicitly mentioned

Consider the user's current time: {current_time}
Consider the user's time zone: {timezone}

Resolve relative time references like "tomorrow", "next week", etc. based on the current time.
For terms like "morning", "afternoon", "evening", use these defaults unless otherwise specified:
- Morning: 9:00-12:00
- Afternoon: 12:00-17:00
- Evening: 17:00-21:00

Response format:
```json
{
  "start_date": "YYYY-MM-DD", // or null if not specified
  "start_time": "HH:MM", // or null if not specified
  "duration_minutes": X, // integer, or null if not specified
  "end_time": "HH:MM" // or null if not specified
}
```
Include only the JSON in your response, no explanations.
"""

# Prompt for extracting attendee information
ATTENDEE_EXTRACTION_PROMPT = """
Extract the names and/or email addresses of all attendees mentioned in the following text:
"{text}"

Exclude the user themselves (assume they are automatically included).
If there are references to "me", "I", or similar, these refer to the user and should be excluded.

Response format:
```json
{
  "attendees": [
    {"name": "Full Name", "email": "email@example.com"}, 
    {"name": "Another Person", "email": null} // if only name is provided
  ]
}
```

If no attendees are mentioned, return an empty array:
```json
{
  "attendees": []
}
```

Include only the JSON in your response, no explanations.
"""

# Prompt for extracting event details
EVENT_EXTRACTION_PROMPT = """
Extract event details from the following text:
"{text}"

Response format:
```json
{
  "summary": "Event title/summary", // or null if not specified
  "description": "Event description", // or null if not specified
  "location": "Event location" // or null if not specified
}
```

Focus on identifying:
1. The main purpose or title of the event (summary)
2. Any details about what the event is about (description)
3. Where the event will take place, physical or virtual (location)

Include only the JSON in your response, no explanations.
"""
