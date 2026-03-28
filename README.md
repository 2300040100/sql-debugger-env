# SQL Query Debugger — OpenEnv Environment

An OpenEnv-compatible reinforcement learning environment where AI agents
learn to debug broken SQL queries. Given a SQLite database schema and a
broken SQL query, the agent must identify and fix the bug to produce the
correct output.

---

## Why this environment matters

Every developer and data analyst debugs SQL daily. A model that can
reliably fix broken SQL queries has immediate real-world value. This
environment provides a clean, deterministic training and evaluation signal
for teaching agents SQL debugging skills — from simple syntax errors to
subtle NULL-handling bugs that trip up even experienced developers.

---

## Environment description

The agent receives a broken SQL query and the database schema. It must
return a fixed query. The environment runs the fixed query against a live
SQLite database and scores the result with partial credit.

**What makes this environment special:**
- Graders are 100% deterministic — SQLite either returns the right rows or it does not
- Partial credit rewards progress — the agent gets signal even for partial fixes
- Three tasks cover a realistic difficulty range from beginner to frontier-model-challenging
- No external dependencies — SQLite is built into Python

---

## Observation space

The agent receives a JSON object with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Which task is running |
| `broken_query` | string | The SQL query that contains a bug |
| `schema_description` | string | Human-readable table and column definitions |
| `error_message` | string or null | Error from running the broken query (if any) |
| `expected_columns` | list of strings | Column names the correct result must have |
| `expected_row_count` | integer | Number of rows the correct result must have |
| `hint` | string or null | Hint shown after the first failed attempt |
| `step_number` | integer | Current step (starts at 0) |
| `max_steps` | integer | Maximum steps allowed for this task |
| `previous_attempt` | string or null | The agent's last submitted query |
| `previous_score` | float or null | Score from the last attempt |

---

## Action space

The agent sends a JSON object with these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fixed_query` | string | Yes | The corrected SQL query |
| `reasoning` | string | No | Optional explanation of what was fixed |

---

## Reward function

Rewards are given with **partial credit** at every step:

| Condition | Reward |
|-----------|--------|
| Query runs without any SQL error | +0.3 |
| Columns match AND row count matches | +0.3 |
| Every row matches the expected output exactly | +0.4 |
| **Perfect fix** | **1.0** |
| Query has a syntax or runtime error | 0.0 |

Rewards are dense — the agent receives signal at every attempt, not just
at the end of the episode. This makes the environment suitable for
reinforcement learning with policy gradient methods.

---

## Tasks

### Task 1 — Fix syntax error (Easy)
**ID:** `task_syntax`  
**Max steps:** 3  
**Expected difficulty:** Any model should solve this in 1–2 attempts.

The agent must fix a missing comma in a SELECT clause. This is the most
common SQL beginner mistake. The broken query runs but returns wrong
columns because SQL interprets `SELECT name salary` as selecting `salary`
with alias `name`.

**Broken query:**
```sql
SELECT name salary FROM employees WHERE salary > 50000;
```
**Bug:** Missing comma between `name` and `salary`  
**Fix:** `SELECT name, salary FROM employees WHERE salary > 50000;`

---

### Task 2 — Fix logic bug (Medium)
**ID:** `task_logic`  
**Max steps:** 5  
**Expected difficulty:** Most models solve this in 1–2 attempts.

The agent must change a LEFT JOIN to an INNER JOIN. The broken query
returns NULL rows for orders with no matching customer. The agent must
understand join semantics to fix this correctly.

**Bug:** `LEFT JOIN` includes unmatched rows  
**Fix:** Change to `INNER JOIN`

---

### Task 3 — Fix NULL and aggregation bug (Hard)
**ID:** `task_advanced`  
**Max steps:** 7  
**Expected difficulty:** Challenges frontier models — requires understanding
of how SQLite's AVG() silently ignores NULLs and how COALESCE() solves it.

The broken query computes an average bonus per department but silently
ignores NULL bonuses, producing a misleadingly high average. The agent
must use `COALESCE(bonus, 0)` to treat NULL as zero.

**Bug:** `AVG(bonus)` ignores NULLs  
**Fix:** `AVG(COALESCE(bonus, 0))`

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — returns 200 if server is running |
| POST | `/reset` | Start a new episode. Body: `{"task_id": "task_syntax"}` |
| POST | `/step` | Submit a fix. Body: `{"fixed_query": "SELECT ..."}` |
| GET | `/state` | Current environment state |
| GET | `/tasks` | List all tasks with action schema |
| POST | `/grader` | Get final score for current episode |
| POST | `/baseline` | Run baseline agent on all 3 tasks |

Interactive docs available at: `http://your-url/docs`

---

## Setup and usage

### Option 1 — Run with Docker (recommended)
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/sql-debugger-env
cd sql-debugger-env
docker build -t sql-debugger-env .
docker run -p 7860:7860 sql-debugger-env
```

### Option 2 — Run with Python directly
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/sql-debugger-env
cd sql-debugger-env
pip install -r requirements.txt
python server/app.py
```

Server starts at `http://localhost:7860`

### Run the baseline script
```bash
# With OpenAI API key (uses GPT-4o-mini as agent):
set OPENAI_API_KEY=your-key-here   # Windows
export OPENAI_API_KEY=your-key-here  # Mac/Linux
python baseline.py

# Without API key (uses deterministic fallback answers):
python baseline.py
```

### Quick test with curl
```bash
# Start episode
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_syntax"}'

# Submit a fix
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"fixed_query": "SELECT name, salary FROM employees WHERE salary > 50000;"}'

# Get score
curl -X POST http://localhost:7860/grader
```

---

## Baseline scores

Scores produced by running `python baseline.py` with deterministic fallback agent:

| Task | Difficulty | Score |
|------|------------|-------|
| task_syntax | Easy | 1.0000 |
| task_logic | Medium | 1.0000 |
| task_advanced | Hard | 1.0000 |
| **Average** | | **1.0000** |

These scores are fully reproducible — the grader is deterministic
(SQLite row comparison) and the fallback agent always submits the
known correct query.

---

## Project structure
```
sql-debugger-env/
├── env/
│   ├── __init__.py         # package exports
│   ├── models.py           # Pydantic Observation, Action, Reward models
│   ├── environment.py      # core env logic: reset(), step(), state()
│   └── tasks.py            # 3 task definitions with correct answers
├── server/
│   └── app.py              # FastAPI server with all required endpoints
├── baseline.py             # baseline inference script
├── openenv.yaml            # OpenEnv metadata
├── Dockerfile              # containerized deployment
├── requirements.txt        # Python dependencies
└── README.md               # this file
```

---

## License

MIT License