"""
Locust load test for SatQuery normal API/database paths.

Measures realistic SIH traffic against the FastAPI backend:

* POST /api/auth/register      (one-time session bootstrap)
* POST /api/auth/login         (authenticate existing session)
* POST /api/chats              (create a conversation)
* POST /api/query              (normal analysis request - primary measured op)
* GET  /api/conversations      (list conversations)
* GET  /api/conversations/{id} (open a conversation with message history)

Heavyweight AI/VLM inference happens on the /api/analysis and /api/query
paths only when AI_MODE=real; with the mock service this file measures the
normal API/database request path (serialization, auth, DB, pooling).

Run per concurrency level (see run_load_test.sh), or interactively:

    locust -f backend/tests/load_test.py --host http://localhost:8000
"""

import uuid

from locust import HttpUser, between, task


class SatQueryUser(HttpUser):
    wait_time = between(0.1, 0.3)
    host = "http://localhost:8000"

    def on_start(self):
        self.email = f"load_{uuid.uuid4().hex[:12]}@loadmailx.io"
        self.password = "loadtestpass1"
        self.access_token = None
        self.chat_id = None

        resp = self.client.post(
            "/api/auth/register",
            json={"email": self.email, "password": self.password},
            name="POST /api/auth/register",
        )
        if resp.status_code < 300:
            self.access_token = resp.json().get("access_token")
        else:
            self.access_token = self._login()

        self._headers = {"Authorization": f"Bearer {self.access_token}"}

        if self.access_token:
            self._create_chat()

    def _login(self):
        resp = self.client.post(
            "/api/auth/login",
            json={"email": self.email, "password": self.password},
            name="POST /api/auth/login",
        )
        if resp.status_code < 300:
            return resp.json().get("access_token")
        return None

    def _create_chat(self):
        resp = self.client.post(
            "/api/chats",
            json={"title": f"load test {self.email}"},
            headers=self._headers,
            name="POST /api/chats",
        )
        if resp.status_code < 300:
            self.chat_id = resp.json().get("id")
            self.chat_url = f"/api/chats/{self.chat_id}"

    @task(6)
    def send_query(self):
        if not self.access_token or not self.chat_id:
            return
        self.client.post(
            "/api/query",
            json={
                "conversation_id": str(self.chat_id),
                "query": "Detect water bodies",
                "image_ids": [],
            },
            headers=self._headers,
            name="POST /api/query",
        )

    @task(2)
    def list_conversations(self):
        if not self.access_token:
            return
        self.client.get(
            "/api/conversations",
            headers=self._headers,
            name="GET /api/conversations",
        )

    @task(1)
    def open_conversation(self):
        if not self.access_token or not self.chat_id:
            return
        self.client.get(
            "/api/conversations/%d" % self.chat_id,
            headers=self._headers,
            name="GET /api/conversations/{id}",
        )

    @task(1)
    def get_chat(self):
        if not self.access_token or not self.chat_id:
            return
        self.client.get(
            self.chat_url,
            headers=self._headers,
            name="GET /api/chats/{id}",
        )