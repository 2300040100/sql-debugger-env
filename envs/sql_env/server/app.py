# envs/sql_env/server/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from envs.sql_env.models import SQLAction, SQLObservation, SQLState
from envs.sql_env.server.sql_environment import SQLDebuggerEnvironment, TASKS

app = FastAPI(
    title="SQL Query Debugger",
    description="OpenEnv environment for debugging broken SQL queries.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = SQLDebuggerEnvironment()


class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_syntax"


class StepRequest(BaseModel):
    fixed_query: str
    reasoning: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "healthy", "service": "sql-debugger-env"}


@app.post("/reset")
def reset(request: ResetRequest = None):
    task_id = "task_syntax"
    if request and request.task_id:
        task_id = request.task_id
    obs = env.reset(task_id=task_id)
    return obs.dict()


@app.post("/step")
def step(request: StepRequest):
    action = SQLAction(
        fixed_query=request.fixed_query,
        reasoning=request.reasoning
    )
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.dict(),
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def state():
    return env.state.dict()


@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                "id": tid,
                "name": t["name"],
                "difficulty": t["difficulty"],
                "description": t["description"],
                "max_steps": t["max_steps"],
            }
            for tid, t in TASKS.items()
        ]
    }


@app.post("/grader")
def grader():
    score = round(min(max(env.best_score, 0.01), 0.99), 4)
    return {
        "task_id": env.task_id,
        "score": score,
        "difficulty": env.task.get("difficulty", ""),
        "steps_taken": env.step_count,
        "solved": env.best_score >= 0.95,
    }


@app.post("/baseline")
def baseline():
    results = {}
    test_env = SQLDebuggerEnvironment()
    for task_id, task_data in TASKS.items():
        test_env.reset(task_id=task_id)
        action = SQLAction(fixed_query=task_data["correct_query"])
        _, reward, _, _ = test_env.step(action)
        results[task_id] = {
            "score": round(min(max(reward, 0.01), 0.99), 4),
            "difficulty": task_data["difficulty"],
        }
    return {"scores": results}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()