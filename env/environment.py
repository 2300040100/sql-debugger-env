# env/environment.py
#
# This is the BRAIN of your environment.
# It manages the database, runs queries, scores them, and tracks state.
#
# KEY CONCEPT: SQLite is Python's built-in database.
# "in-memory" means the database only lives in RAM during the episode.
# Every reset() creates a brand new clean database. No files needed.

import sqlite3                    # built into Python — no pip install needed
from typing import Tuple, List, Any, Optional
from .models import Observation, Action, Reward
from .tasks import TASKS


class SQLDebuggerEnv:
    """
    The SQL Query Debugger environment.

    An episode works like this:
      1. Call reset(task_id) → get an Observation (the broken query + schema)
      2. Agent reads the Observation and sends back an Action (fixed_query)
      3. Call step(action) → runs the query, scores it, returns new Observation + reward
      4. Repeat step 2-3 until done=True
      5. Call state() anytime to see current status
    """

    def __init__(self):
        # These will be set properly when reset() is called
        self.task_id: str = "task_syntax"
        self.task: dict = {}
        self.step_count: int = 0
        self.done: bool = False
        self.db_connection: Optional[sqlite3.Connection] = None
        self.previous_attempt: Optional[str] = None
        self.previous_score: Optional[float] = None
        self.best_score: float = 0.0        # tracks best score across all steps
        self.episode_actions: list = []     # stores all actions taken this episode

    # ─────────────────────────────────────────────────────────────
    # reset() — Start a brand new episode
    # Called at the beginning of every episode.
    # Returns the first Observation the agent will see.
    # ─────────────────────────────────────────────────────────────
    def reset(self, task_id: str = "task_syntax") -> Observation:
        """
        Resets the environment for a new episode.
        Creates a fresh SQLite database with the task's tables and data.
        Returns the starting Observation.
        """
        # Validate the task_id
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS.keys())}")

        # Store the task
        self.task_id = task_id
        self.task = TASKS[task_id]

        # Reset all tracking variables
        self.step_count = 0
        self.done = False
        self.previous_attempt = None
        self.previous_score = None
        self.best_score = 0.0
        self.episode_actions = []

        # Close any old database connection first
        if self.db_connection:
            self.db_connection.close()

        # Create a FRESH in-memory SQLite database
        # ":memory:" means it lives in RAM — fast, no files
        self.db_connection = sqlite3.connect(":memory:")

        # Run the setup SQL to create tables and insert data
        self.db_connection.executescript(self.task["setup_sql"])
        self.db_connection.commit()

        # Return the starting observation
        return self._build_observation()

    # ─────────────────────────────────────────────────────────────
    # step() — Agent sends a fixed query, we score it
    # This is called every time the agent makes an attempt.
    # Returns: (observation, reward_value, done, info_dict)
    # ─────────────────────────────────────────────────────────────
    def step(self, action: Action) -> Tuple[Observation, float, bool, dict]:
        """
        Runs the agent's fixed_query against the SQLite database.
        Scores the result. Returns next observation, reward, done flag, and info.
        """
        if self.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        # Save this attempt for the next observation
        self.previous_attempt = action.fixed_query
        self.episode_actions.append(action)

        # Score the agent's query
        reward = self._compute_reward(action.fixed_query)
        self.previous_score = reward.total

        # Track the best score this episode
        self.best_score = max(self.best_score, reward.total)

        # Advance step counter
        self.step_count += 1

        # Episode ends if: agent got perfect score OR used all steps OR query is perfect
        if reward.total == 1.0 or self.step_count >= self.task["max_steps"]:
            self.done = True

        # Build the next observation
        obs = self._build_observation()

        # Info dict gives extra detail (not used for training, just for debugging)
        info = {
            "reward_breakdown": reward.dict(),
            "step": self.step_count,
            "best_score_so_far": self.best_score,
        }

        return obs, reward.total, self.done, info

    # ─────────────────────────────────────────────────────────────
    # state() — Snapshot of current state
    # Required by OpenEnv spec.
    # ─────────────────────────────────────────────────────────────
    def state(self) -> dict:
        """Returns the current state as a plain dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task.get("name", ""),
            "difficulty": self.task.get("difficulty", ""),
            "step_count": self.step_count,
            "max_steps": self.task.get("max_steps", 0),
            "done": self.done,
            "best_score": self.best_score,
            "previous_score": self.previous_score,
            "previous_attempt": self.previous_attempt,
            "total_attempts": len(self.episode_actions),
        }

    # ─────────────────────────────────────────────────────────────
    # _compute_reward() — The scoring engine
    # PRIVATE method (underscore prefix = internal use only)
    # ─────────────────────────────────────────────────────────────
    def _compute_reward(self, query: str) -> Reward:
        """
        Scores the agent's query with partial credit:
          +0.3 if the query runs without any SQL error
          +0.3 if columns match AND row count matches
          +0.4 if every row matches exactly (perfect answer)
        Total possible: 1.0
        """
        runs_score = 0.0
        shape_score = 0.0
        exact_score = 0.0
        agent_output = None
        message_parts = []

        # ── Step A: Try running the agent's query ──
        try:
            cursor = self.db_connection.execute(query)
            agent_rows = cursor.fetchall()
            agent_columns = [desc[0] for desc in cursor.description] if cursor.description else []
            agent_output = agent_rows

            # Query ran without error → +0.3
            runs_score = 0.3
            message_parts.append("✓ Query runs without error (+0.3)")

        except sqlite3.Error as e:
            # Query has a syntax or runtime error → 0 points
            message_parts.append(f"✗ Query failed with error: {str(e)} (+0.0)")
            return Reward(
                total=0.0,
                runs_without_error=0.0,
                shape_matches=0.0,
                exact_match=0.0,
                message=" | ".join(message_parts),
                agent_output=None,
            )

        # ── Step B: Get the EXPECTED output by running the correct query ──
        expected_cursor = self.db_connection.execute(self.task["correct_query"])
        expected_rows = expected_cursor.fetchall()
        expected_columns = self.task["expected_columns"]
        expected_row_count = self.task["expected_row_count"]

        # ── Step C: Check if columns and row count match ──
        columns_match = (
            len(agent_columns) == len(expected_columns) and
            [c.lower() for c in agent_columns] == [c.lower() for c in expected_columns]
        )
        row_count_match = (len(agent_rows) == expected_row_count)

        if columns_match and row_count_match:
            shape_score = 0.3
            message_parts.append("✓ Columns and row count match (+0.3)")
        else:
            if not columns_match:
                message_parts.append(
                    f"✗ Column mismatch: got {agent_columns}, expected {expected_columns} (+0.0)"
                )
            if not row_count_match:
                message_parts.append(
                    f"✗ Row count mismatch: got {len(agent_rows)}, expected {expected_row_count} (+0.0)"
                )

        # ── Step D: Check if every single row matches exactly ──
        # Sort both result sets so order doesn't matter
        if columns_match and row_count_match:
            agent_sorted = sorted(agent_rows)
            expected_sorted = sorted(expected_rows)

            if agent_sorted == expected_sorted:
                exact_score = 0.4
                message_parts.append("✓ All rows match exactly (+0.4)")
            else:
                message_parts.append("✗ Rows do not match exactly (+0.0)")

        # ── Final score ──
        total = round(runs_score + shape_score + exact_score, 4)

        return Reward(
            total=total,
            runs_without_error=runs_score,
            shape_matches=shape_score,
            exact_match=exact_score,
            message=" | ".join(message_parts),
            agent_output=[list(row) for row in (agent_output or [])],
        )

    # ─────────────────────────────────────────────────────────────
    # _build_observation() — Assembles the Observation object
    # Called after reset() and after every step()
    # ─────────────────────────────────────────────────────────────
    def _build_observation(self) -> Observation:
        """Builds the Observation the agent receives."""
        return Observation(
            task_id=self.task_id,
            broken_query=self.task["broken_query"],
            schema_description=self._get_schema_description(),
            error_message=self._get_error_message(self.previous_attempt),
            expected_columns=self.task["expected_columns"],
            expected_row_count=self.task["expected_row_count"],
            hint=self.task.get("hint") if self.step_count > 0 else None,
            step_number=self.step_count,
            max_steps=self.task["max_steps"],
            previous_attempt=self.previous_attempt,
            previous_score=self.previous_score,
        )

    def _get_schema_description(self) -> str:
        """
        Reads the actual table structure from SQLite and returns it as a
        human-readable string. The agent needs this to understand the database.
        """
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = [row[0] for row in cursor.fetchall()]

        schema_parts = []
        for table in tables:
            col_cursor = self.db_connection.execute(f"PRAGMA table_info({table});")
            cols = col_cursor.fetchall()
            col_descriptions = [f"{col[1]} ({col[2]})" for col in cols]
            schema_parts.append(f"Table '{table}': {', '.join(col_descriptions)}")

        return "\n".join(schema_parts)

    def _get_error_message(self, query: Optional[str]) -> Optional[str]:
        """
        Tries running a query and returns the error message if it fails.
        Returns None if the query runs fine (or if no previous attempt).
        """
        if not query:
            return None
        try:
            self.db_connection.execute(query)
            return None
        except sqlite3.Error as e:
            return str(e)

    def close(self):
        """Clean up the database connection."""
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
