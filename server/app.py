# server/app.py
#
# FastAPI turns your Python environment into a web server.
# Each function with @app.get or @app.post becomes a URL endpoint.
# When someone visits that URL, FastAPI calls your function and returns the result as JSON.
#
# KEY CONCEPT: We keep ONE environment instance per "session" in a dictionary.


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent folder to path so we can import 'env'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import SQLDebuggerEnv, Action, TASKS

# ── Create the FastAPI app ──
app = FastAPI(
    title="SQL Query Debugger Environment",
    description="An OpenEnv environment where AI agents learn to debug broken SQL queries.",
    version="1.0.0",
)

# ── Allow requests from anywhere (needed for HF Spaces) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── One global environment instance ──
# In production you'd have one per session
env = SQLDebuggerEnv()
current_task_id = "task_syntax"  # tracks which task is active


# ════════════════════════════════════════════════════════
# REQUEST MODELS
# These define what JSON the server expects to receive
# ════════════════════════════════════════════════════════

class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_syntax"

class StepRequest(BaseModel):
    fixed_query: str
    reasoning: Optional[str] = None


# ════════════════════════════════════════════════════════
# ENDPOINT 1: GET /health
# Must return 200 OK. That's it.
# ════════════════════════════════════════════════════════

@app.get("/health")
def health():
    """Health check — returns 200 if server is running."""
    return {"status": "ok", "environment": "sql-query-debugger"}


# ════════════════════════════════════════════════════════
# ENDPOINT 2: POST /reset
# Starts a fresh episode.
# ════════════════════════════════════════════════════════

@app.post("/reset")
def reset(request: ResetRequest = None):
    global current_task_id
    
    task_id = "task_syntax"
    if request and request.task_id:
        task_id = request.task_id
    
    if task_id not in TASKS:
        task_id = "task_syntax"
    
    current_task_id = task_id
    observation = env.reset(task_id=task_id)
    return observation.dict()


# ════════════════════════════════════════════════════════
# ENDPOINT 3: POST /step
# Agent sends its fixed query here.
# Returns new observation, reward, done flag, and info.
# ════════════════════════════════════════════════════════

@app.post("/step")
def step(request: StepRequest):
    """
    Takes the agent's action (fixed SQL query) and returns the result.
    Send: { "fixed_query": "SELECT name, salary FROM employees WHERE salary > 50000;" }
    Returns: { observation, reward, done, info }
    """
    if env.done:
        raise HTTPException(
            status_code=400,
            detail="Episode is already done. Call /reset first."
        )

    action = Action(
        fixed_query=request.fixed_query,
        reasoning=request.reasoning
    )

    observation, reward, done, info = env.step(action)

    return {
        "observation": observation.dict(),
        "reward": reward,
        "done": done,
        "info": info,
    }


# ════════════════════════════════════════════════════════
# ENDPOINT 4: GET /state
# Returns current state snapshot.
# Required by OpenEnv spec.
# ════════════════════════════════════════════════════════

@app.get("/state")
def state():
    """Returns the current environment state."""
    return env.state()


# ════════════════════════════════════════════════════════
# ENDPOINT 5: GET /tasks
# Lists all available tasks with their action schema.
# ════════════════════════════════════════════════════════

@app.get("/tasks")
def tasks():
    """Returns all available tasks and the action schema."""
    task_list = []
    for task_id, task_data in TASKS.items():
        task_list.append({
            "id": task_id,
            "name": task_data["name"],
            "difficulty": task_data["difficulty"],
            "description": task_data["description"],
            "max_steps": task_data["max_steps"],
            "action_schema": Action.schema(),
        })
    return {"tasks": task_list}


# ════════════════════════════════════════════════════════
# ENDPOINT 6: POST /grader
# Runs the grader for the current episode.
# ════════════════════════════════════════════════════════

@app.post("/grader")
def grader():
    """
    Returns the final grader score for the current episode.
    Call this after your episode is done.
    Returns: { "task_id": ..., "score": 0.0-1.0, "breakdown": {...} }
    """
    return {
        "task_id": current_task_id,
        "score": env.best_score,
        "difficulty": TASKS[current_task_id]["difficulty"],
        "steps_taken": env.step_count,
        "breakdown": {
            "best_score_achieved": env.best_score,
            "total_attempts": len(env.episode_actions),
            "solved": env.best_score == 1.0,
        }
    }


# ════════════════════════════════════════════════════════
# ENDPOINT 7: POST /baseline
# Runs the built-in baseline agent on ALL 3 tasks.
# This runs a simple rule-based agent (not an LLM) as the baseline.
# ════════════════════════════════════════════════════════

@app.post("/baseline")
def baseline():
    """
    Runs a deterministic baseline agent on all 3 tasks.
    Returns reproducible scores for each task.
    The baseline agent always submits the correct answer
    (this sets the upper bound — a perfect baseline shows graders work).
    """
    results = {}
    baseline_env = SQLDebuggerEnv()  # fresh env just for baseline

    for task_id in TASKS.keys():
        obs = baseline_env.reset(task_id=task_id)
        correct_query = TASKS[task_id]["correct_query"]

        # Baseline agent: submit the known correct query
        action = Action(fixed_query=correct_query)
        _, reward, _, _ = baseline_env.step(action)

        results[task_id] = {
            "score": reward,
            "difficulty": TASKS[task_id]["difficulty"],
        }

    return {
        "baseline_agent": "deterministic-correct-answer",
        "scores": results,
        "note": "Baseline submits the known correct query for each task."
    }


# ════════════════════════════════════════════════════════
# START THE SERVER
# Port 7860 is REQUIRED for Hugging Face Spaces
# ════════════════════════════════════════════════════════

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
