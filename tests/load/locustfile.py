from locust import HttpUser, task, between
import random
from datetime import datetime, timedelta

class CalendarAssistantUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Initialize user session"""
        # Login and get token
        response = self.client.post("/auth/login", json={
            "email": f"test_user_{random.randint(1, 1000)}@example.com",
            "password": "test_password"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.environment.runner.quit()

    @task(3)
    def get_events(self):
        """Get user's calendar events"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)
        
        self.client.get(
            f"/events?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=self.headers
        )

    @task(2)
    def create_event(self):
        """Create a new calendar event"""
        start_time = datetime.now() + timedelta(days=random.randint(1, 30))
        end_time = start_time + timedelta(hours=random.randint(1, 4))
        
        event_data = {
            "title": f"Test Event {random.randint(1, 1000)}",
            "description": "Load test event",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "location": "Virtual Meeting",
            "attendees": [f"attendee_{i}@example.com" for i in range(3)]
        }
        
        self.client.post("/events", json=event_data, headers=self.headers)

    @task(1)
    def update_event(self):
        """Update an existing event"""
        # First get events
        response = self.client.get("/events", headers=self.headers)
        if response.status_code == 200 and response.json():
            event_id = random.choice(response.json())["id"]
            
            # Update the event
            update_data = {
                "title": f"Updated Event {random.randint(1, 1000)}",
                "description": "Updated load test event"
            }
            
            self.client.put(f"/events/{event_id}", json=update_data, headers=self.headers)

    @task(1)
    def delete_event(self):
        """Delete an event"""
        # First get events
        response = self.client.get("/events", headers=self.headers)
        if response.status_code == 200 and response.json():
            event_id = random.choice(response.json())["id"]
            self.client.delete(f"/events/{event_id}", headers=self.headers)

    @task(2)
    def get_agent_suggestions(self):
        """Get AI agent suggestions"""
        self.client.get("/agent/suggestions", headers=self.headers)

    @task(1)
    def create_agent_session(self):
        """Create a new agent session"""
        session_data = {
            "goal": "Schedule a team meeting",
            "preferences": {
                "duration": "1 hour",
                "participants": ["team@example.com"],
                "time_range": "next week"
            }
        }
        
        self.client.post("/agent/sessions", json=session_data, headers=self.headers)

    @task(3)
    def get_session_status(self):
        """Get agent session status"""
        # First get active sessions
        response = self.client.get("/agent/sessions", headers=self.headers)
        if response.status_code == 200 and response.json():
            session_id = random.choice(response.json())["id"]
            self.client.get(f"/agent/sessions/{session_id}", headers=self.headers)

class CalendarAssistantLoadTest:
    """Load test configuration"""
    
    def __init__(self):
        self.host = "http://localhost:8000"
        self.users = 100
        self.spawn_rate = 10
        self.run_time = "5m"
        
    def run(self):
        """Run the load test"""
        import subprocess
        
        cmd = [
            "locust",
            "-f", "locustfile.py",
            "--host", self.host,
            "--users", str(self.users),
            "--spawn-rate", str(self.spawn_rate),
            "--run-time", self.run_time,
            "--headless"
        ]
        
        subprocess.run(cmd)

if __name__ == "__main__":
    test = CalendarAssistantLoadTest()
    test.run() 