# envs/sql_env/client.py
# Client for the SQL Query Debugger environment
# Usage:
#   from envs.sql_env.client import SQLDebuggerClient
#   client = SQLDebuggerClient(base_url="https://karishma2026-sql-debugger-env.hf.space")
#   obs = client.reset(task_id="task_syntax")
#   result = client.step(fixed_query="SELECT name, salary FROM employees WHERE salary > 50000;")

import requests
from typing import Optional
from .models import SQLAction, SQLObservation, SQLState


class SQLDebuggerClient:
    """
    Client for the SQL Query Debugger OpenEnv environment.
    Connects to the environment server via HTTP.
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health(self) -> dict:
        """Check if server is running."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def reset(self, task_id: str = "task_syntax") -> SQLObservation:
        """Reset the environment and return initial observation."""
        response = self.session.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id}
        )
        response.raise_for_status()
        return SQLObservation(**response.json())

    def step(self, fixed_query: str, reasoning: Optional[str] = None):
        """Submit a fixed query and get observation, reward, done, info."""
        action = SQLAction(fixed_query=fixed_query, reasoning=reasoning)
        response = self.session.post(
            f"{self.base_url}/step",
            json=action.dict()
        )
        response.raise_for_status()
        data = response.json()
        return (
            SQLObservation(**data["observation"]),
            data["reward"],
            data["done"],
            data["info"],
        )

    def state(self) -> SQLState:
        """Get current environment state."""
        response = self.session.get(f"{self.base_url}/state")
        response.raise_for_status()
        return SQLState(**response.json())

    def tasks(self) -> dict:
        """List all available tasks."""
        response = self.session.get(f"{self.base_url}/tasks")
        response.raise_for_status()
        return response.json()

    def grader(self) -> dict:
        """Get final score for current episode."""
        response = self.session.post(f"{self.base_url}/grader")
        response.raise_for_status()
        return response.json()

    def close(self):
        """Close the client session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()