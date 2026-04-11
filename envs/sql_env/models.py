# envs/sql_env/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class SQLAction(BaseModel):
    """Action the agent takes — submit a fixed SQL query."""
    fixed_query: str = Field(
        description="The corrected SQL query string."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Optional explanation of what was fixed."
    )


class SQLObservation(BaseModel):
    """What the agent sees at each step."""
    task_id: str
    broken_query: str
    schema_description: str
    error_message: Optional[str] = None
    expected_columns: List[str]
    expected_row_count: int
    hint: Optional[str] = None
    step_number: int
    max_steps: int
    previous_attempt: Optional[str] = None
    previous_score: Optional[float] = None


class SQLState(BaseModel):
    """Current state of the environment."""
    task_id: str
    task_name: str
    difficulty: str
    step_count: int
    max_steps: int
    done: bool
    best_score: float
    episode_id: str