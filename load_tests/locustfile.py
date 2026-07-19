import uuid
from locust import HttpUser, task, between

class NakshatraLoadTestUser(HttpUser):
    # Wait between 1 and 3 seconds between tasks to simulate human pacing
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user is spawned. Initializes session and generates a Kundli."""
        self.session_id = f"test-session-{uuid.uuid4()}"
        self.headers = {
            "X-Session-Id": self.session_id,
            "Content-Type": "application/json"
        }
        
        # 1. Create/Initialize session
        self.client.post("/sessions", json={
            "session_id": self.session_id
        }, headers=self.headers)
        
        # 2. Generate Kundli (simulating form submission)
        # Note: We use dummy coordinates and details.
        self.client.post("/kundli", json={
            "fullName": "Load Test User",
            "gender": "Male",
            "dob": "1995-05-15",
            "tob": "08:30:00",
            "lat": 28.6139,
            "lon": 77.2090,
            "timezone": "Asia/Kolkata",
            "place": "New Delhi, Delhi, India"
        }, headers=self.headers)

    @task(3)
    def chat_message(self):
        """Simulate chatting with Nakshatra AI. Hits /chat and tests LLM failovers + rate limits."""
        self.client.post("/chat", json={
            "query": "What does my chart say about my future career and success?"
        }, headers=self.headers)

    @task(1)
    def check_ping(self):
        """Simulate health checks or lightweight API checks (minimal overhead)."""
        self.client.get("/ping", headers=self.headers)
