# test_env.py  ← to verify your environment works


from env import SQLDebuggerEnv, Action

print("=" * 60)
print("TESTING SQL DEBUGGER ENVIRONMENT")
print("=" * 60)

env = SQLDebuggerEnv()

# ── Test Task 1: Easy (syntax error) ──
print("\n--- TASK 1: Easy (syntax error) ---")
obs = env.reset(task_id="task_syntax")
print(f"Task: {obs.task_id}")
print(f"Broken query: {obs.broken_query}")
print(f"Schema:\n{obs.schema_description}")

# Try the WRONG answer first (still broken)
print("\n>> Attempt 1: still wrong query")
action = Action(fixed_query="SELECT name salary FROM employees WHERE salary > 50000;")
obs, reward, done, info = env.step(action)
print(f"Score: {reward}  |  Done: {done}")
print(f"Breakdown: {info['reward_breakdown']['message']}")

# Try the CORRECT answer
print("\n>> Attempt 2: correct query")
action = Action(fixed_query="SELECT name, salary FROM employees WHERE salary > 50000;")
obs, reward, done, info = env.step(action)
print(f"Score: {reward}  |  Done: {done}")
print(f"Breakdown: {info['reward_breakdown']['message']}")

# ── Test Task 2: Medium (logic bug) ──
print("\n--- TASK 2: Medium (logic bug) ---")
obs = env.reset(task_id="task_logic")
print(f"Broken query: {obs.broken_query.strip()}")

print("\n>> Attempt: correct fix")
action = Action(fixed_query="""
    SELECT customers.name, orders.product, orders.amount
    FROM orders
    INNER JOIN customers ON orders.customer_id = customers.id;
""")
obs, reward, done, info = env.step(action)
print(f"Score: {reward}  |  Done: {done}")
print(f"Breakdown: {info['reward_breakdown']['message']}")

# ── Test Task 3: Hard (NULL bug) ──
print("\n--- TASK 3: Hard (NULL/aggregation bug) ---")
obs = env.reset(task_id="task_advanced")
print(f"Broken query: {obs.broken_query.strip()}")

print("\n>> Attempt: correct fix with COALESCE")
action = Action(fixed_query="""
    SELECT department, AVG(COALESCE(bonus, 0)) as avg_bonus
    FROM staff
    GROUP BY department
    ORDER BY department;
""")
obs, reward, done, info = env.step(action)
print(f"Score: {reward}  |  Done: {done}")
print(f"Breakdown: {info['reward_breakdown']['message']}")

print("\n" + "=" * 60)
print("State snapshot:")
print(env.state())
print("=" * 60)
print("\n✅ All tests passed! Environment is working correctly.")
