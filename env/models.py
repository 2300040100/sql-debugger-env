# env/models.py
# Pydantic models = typed data containers with automatic validation.
# Think of them like strict dictionaries that reject wrong types.

from pydantic import BaseModel, Field
from typing import Optional, List, Any

class Observation(BaseModel):
    """
    What the agent SEES at every step.
    The agent reads this and decides what action to take.
    """
    task_id: str                        # which task is running: "task_syntax", "task_logic", "task_advanced"
    broken_query: str                   # the SQL query that has a bug in it
    schema_description: str            # description of the database tables and columns
    error_message: Optional[str]       # if the broken query was run, what error came back (or None)
    expected_columns: List[str]        # the column names the correct result should have
    expected_row_count: int            # how many rows the correct result should have
    hint: Optional[str]                # optional hint for harder tasks
    step_number: int                   # which step we are on (starts at 0)
    max_steps: int                     # how many steps the agent gets total
    previous_attempt: Optional[str]    # the agent's last query attempt (None on first step)
    previous_score: Optional[float]    # the score from the last attempt (None on first step)

class Action(BaseModel):
    """
    What the agent SENDS BACK — its answer.
    The agent just needs to return a fixed SQL query.
    """
    fixed_query: str = Field(
        description="The corrected SQL query. Must be valid SQLite SQL.",
        min_length=1
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Optional: explain what bug you found and how you fixed it."
    )

class Reward(BaseModel):
    """
    The score breakdown after each step.
    We give partial credit so the agent can learn gradually.
    """
    total: float                        # final score between 0.0 and 1.0
    runs_without_error: float          # +0.3 if the query runs at all
    shape_matches: float               # +0.3 if columns and row count are correct
    exact_match: float                 # +0.4 if every row matches exactly
    message: str                       # human-readable explanation of the score
    agent_output: Optional[List[Any]]  # what the agent's query actually returned