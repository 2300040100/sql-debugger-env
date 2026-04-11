# envs/sql_env/server/sql_environment.py
import sqlite3
import uuid
from typing import Optional, Tuple
from ..models import SQLAction, SQLObservation, SQLState

TASKS = {
    "task_syntax": {
        "name": "Fix syntax error",
        "difficulty": "easy",
        "max_steps": 3,
        "description": "Fix the missing comma in SELECT clause.",
        "hint": "Look carefully at the SELECT clause — something is missing between column names.",
        "setup_sql": """
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary INTEGER
            );
            INSERT INTO employees VALUES (1, 'Alice', 'Engineering', 90000);
            INSERT INTO employees VALUES (2, 'Bob', 'Marketing', 45000);
            INSERT INTO employees VALUES (3, 'Carol', 'Engineering', 75000);
            INSERT INTO employees VALUES (4, 'Dave', 'HR', 52000);
        """,
        "broken_query": "SELECT name salary FROM employees WHERE salary > 50000;",
        "correct_query": "SELECT name, salary FROM employees WHERE salary > 50000;",
        "expected_columns": ["name", "salary"],
        "expected_row_count": 3,
    },
    "task_logic": {
        "name": "Fix logic bug",
        "difficulty": "medium",
        "max_steps": 5,
        "description": "Fix the JOIN type to exclude unmatched rows.",
        "hint": "Think about the difference between LEFT JOIN and INNER JOIN.",
        "setup_sql": """
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT
            );
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                product TEXT,
                amount REAL
            );
            INSERT INTO customers VALUES (1, 'Alice', 'Delhi');
            INSERT INTO customers VALUES (2, 'Bob', 'Mumbai');
            INSERT INTO orders VALUES (1, 1, 'Laptop', 1200.00);
            INSERT INTO orders VALUES (2, 2, 'Phone', 800.00);
            INSERT INTO orders VALUES (3, 99, 'Tablet', 500.00);
        """,
        "broken_query": """SELECT customers.name, orders.product, orders.amount
FROM orders
LEFT JOIN customers ON orders.customer_id = customers.id;""",
        "correct_query": """SELECT customers.name, orders.product, orders.amount
FROM orders
INNER JOIN customers ON orders.customer_id = customers.id;""",
        "expected_columns": ["name", "product", "amount"],
        "expected_row_count": 2,
    },
    "task_advanced": {
        "name": "Fix NULL aggregation bug",
        "difficulty": "hard",
        "max_steps": 7,
        "description": "Fix AVG() to treat NULL bonus as 0 using COALESCE.",
        "hint": "Look up COALESCE() in SQLite — it replaces NULL with a default value.",
        "setup_sql": """
            CREATE TABLE staff (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                bonus REAL
            );
            INSERT INTO staff VALUES (1, 'Alice', 'Engineering', 5000);
            INSERT INTO staff VALUES (2, 'Bob', 'Engineering', NULL);
            INSERT INTO staff VALUES (3, 'Carol', 'Engineering', 3000);
            INSERT INTO staff VALUES (4, 'Dave', 'HR', NULL);
            INSERT INTO staff VALUES (5, 'Eve', 'HR', 2000);
        """,
        "broken_query": """SELECT department, AVG(bonus) as avg_bonus
FROM staff
GROUP BY department
ORDER BY department;""",
        "correct_query": """SELECT department, AVG(COALESCE(bonus, 0)) as avg_bonus
FROM staff
GROUP BY department
ORDER BY department;""",
        "expected_columns": ["department", "avg_bonus"],
        "expected_row_count": 2,
    },
    "task_boundary": {
        "name": "Fix boundary condition bug",
        "difficulty": "easy",
        "max_steps": 3,
        "description": "Fix >= vs > boundary condition.",
        "hint": "Check the comparison operator — should it be > or >=?",
        "setup_sql": """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                stock INTEGER,
                price REAL
            );
            INSERT INTO products VALUES (1, 'Laptop', 'Electronics', 150, 999.99);
            INSERT INTO products VALUES (2, 'Phone', 'Electronics', 100, 699.99);
            INSERT INTO products VALUES (3, 'Tablet', 'Electronics', 80, 499.99);
            INSERT INTO products VALUES (4, 'Headphones', 'Audio', 200, 199.99);
            INSERT INTO products VALUES (5, 'Speaker', 'Audio', 50, 149.99);
        """,
        "broken_query": "SELECT name, stock FROM products WHERE stock > 100;",
        "correct_query": "SELECT name, stock FROM products WHERE stock >= 100;",
        "expected_columns": ["name", "stock"],
        "expected_row_count": 3,
    },
    "task_groupby": {
        "name": "Fix missing GROUP BY",
        "difficulty": "medium",
        "max_steps": 5,
        "description": "Add missing GROUP BY clause for COUNT aggregation.",
        "hint": "When using COUNT() with another column, you need GROUP BY.",
        "setup_sql": """
            CREATE TABLE customers2 (
                id INTEGER PRIMARY KEY,
                name TEXT,
                city TEXT
            );
            CREATE TABLE orders2 (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                product TEXT,
                amount REAL
            );
            INSERT INTO customers2 VALUES (1, 'Alice', 'Delhi');
            INSERT INTO customers2 VALUES (2, 'Bob', 'Mumbai');
            INSERT INTO customers2 VALUES (3, 'Carol', 'Bangalore');
            INSERT INTO orders2 VALUES (1, 1, 'Laptop', 1200.00);
            INSERT INTO orders2 VALUES (2, 1, 'Phone', 800.00);
            INSERT INTO orders2 VALUES (3, 2, 'Tablet', 500.00);
            INSERT INTO orders2 VALUES (4, 3, 'Headphones', 200.00);
            INSERT INTO orders2 VALUES (5, 3, 'Speaker', 150.00);
            INSERT INTO orders2 VALUES (6, 3, 'Charger', 50.00);
        """,
        "broken_query": """SELECT customers2.name, COUNT(orders2.id) as order_count
FROM customers2
INNER JOIN orders2 ON customers2.id = orders2.customer_id;""",
        "correct_query": """SELECT customers2.name, COUNT(orders2.id) as order_count
FROM customers2
INNER JOIN orders2 ON customers2.id = orders2.customer_id
GROUP BY customers2.name
ORDER BY customers2.name;""",
        "expected_columns": ["name", "order_count"],
        "expected_row_count": 3,
    },
    "task_having": {
        "name": "Fix WHERE vs HAVING bug",
        "difficulty": "hard",
        "max_steps": 7,
        "description": "Replace WHERE with HAVING for aggregate filter.",
        "hint": "WHERE filters rows before grouping. HAVING filters groups after aggregation.",
        "setup_sql": """
            CREATE TABLE staff2 (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL
            );
            INSERT INTO staff2 VALUES (1, 'Alice', 'Engineering', 90000);
            INSERT INTO staff2 VALUES (2, 'Bob', 'Engineering', 85000);
            INSERT INTO staff2 VALUES (3, 'Carol', 'Marketing', 55000);
            INSERT INTO staff2 VALUES (4, 'Dave', 'Marketing', 60000);
            INSERT INTO staff2 VALUES (5, 'Eve', 'HR', 45000);
            INSERT INTO staff2 VALUES (6, 'Frank', 'HR', 50000);
        """,
        "broken_query": """SELECT department, AVG(salary) as avg_salary
FROM staff2
GROUP BY department
WHERE AVG(salary) > 60000;""",
        "correct_query": """SELECT department, AVG(salary) as avg_salary
FROM staff2
GROUP BY department
HAVING AVG(salary) > 60000
ORDER BY department;""",
        "expected_columns": ["department", "avg_salary"],
        "expected_row_count": 1,
    },
}


class SQLDebuggerEnvironment:
    """SQL Query Debugger OpenEnv Environment."""

    def __init__(self):
        self.task_id: str = "task_syntax"
        self.task: dict = {}
        self.step_count: int = 0
        self.done: bool = False
        self.db_connection: Optional[sqlite3.Connection] = None
        self.previous_attempt: Optional[str] = None
        self.previous_score: Optional[float] = None
        self.best_score: float = 0.0
        self.episode_id: str = str(uuid.uuid4())

    def reset(self, task_id: str = "task_syntax") -> SQLObservation:
        if task_id not in TASKS:
            task_id = "task_syntax"

        self.task_id = task_id
        self.task = TASKS[task_id]
        self.step_count = 0
        self.done = False
        self.previous_attempt = None
        self.previous_score = None
        self.best_score = 0.0
        self.episode_id = str(uuid.uuid4())

        if self.db_connection:
            self.db_connection.close()

        self.db_connection = sqlite3.connect(":memory:")
        self.db_connection.executescript(self.task["setup_sql"])
        self.db_connection.commit()

        return self._build_observation()

    def step(self, action: SQLAction) -> Tuple[SQLObservation, float, bool, dict]:
        if self.done:
            return self._build_observation(), 0.0, True, {}

        self.previous_attempt = action.fixed_query
        reward, message = self._compute_reward(action.fixed_query)
        self.previous_score = reward
        self.best_score = max(self.best_score, reward)
        self.step_count += 1

        if reward >= 0.95 or self.step_count >= self.task["max_steps"]:
            self.done = True

        return self._build_observation(), reward, self.done, {"message": message}

    @property
    def state(self) -> SQLState:
        return SQLState(
            task_id=self.task_id,
            task_name=self.task.get("name", ""),
            difficulty=self.task.get("difficulty", ""),
            step_count=self.step_count,
            max_steps=self.task.get("max_steps", 0),
            done=self.done,
            best_score=self.best_score,
            episode_id=self.episode_id,
        )

    def _compute_reward(self, query: str):
        runs_score = 0.0
        shape_score = 0.0
        exact_score = 0.0
        parts = []

        try:
            cursor = self.db_connection.execute(query)
            agent_rows = cursor.fetchall()
            agent_cols = [d[0] for d in cursor.description] if cursor.description else []
            runs_score = 0.30
            parts.append("runs ok")
        except sqlite3.Error as e:
            return 0.01, f"error: {e}"

        expected_cursor = self.db_connection.execute(self.task["correct_query"])
        expected_rows = expected_cursor.fetchall()
        expected_cols = self.task["expected_columns"]
        expected_count = self.task["expected_row_count"]

        cols_match = (
            len(agent_cols) == len(expected_cols) and
            [c.lower() for c in agent_cols] == [c.lower() for c in expected_cols]
        )
        count_match = len(agent_rows) == expected_count

        if cols_match and count_match:
            shape_score = 0.30
            parts.append("shape ok")

            if sorted(agent_rows) == sorted(expected_rows):
                exact_score = 0.35
                parts.append("rows match")

                remaining = self.task["max_steps"] - self.step_count
                speed = round(0.04 * remaining / self.task["max_steps"], 4)
                total = round(min(runs_score + shape_score + exact_score + speed, 0.99), 4)
                return total, " | ".join(parts)

        total = round(min(max(runs_score + shape_score + exact_score, 0.01), 0.99), 4)
        return total, " | ".join(parts)

    def _build_observation(self) -> SQLObservation:
        return SQLObservation(
            task_id=self.task_id,
            broken_query=self.task["broken_query"],
            schema_description=self._get_schema(),
            error_message=self._get_error(self.previous_attempt),
            expected_columns=self.task["expected_columns"],
            expected_row_count=self.task["expected_row_count"],
            hint=self.task.get("hint") if self.step_count > 0 else None,
            step_number=self.step_count,
            max_steps=self.task["max_steps"],
            previous_attempt=self.previous_attempt,
            previous_score=self.previous_score,
        )

    def _get_schema(self) -> str:
        cursor = self.db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )
        tables = [r[0] for r in cursor.fetchall()]
        parts = []
        for t in tables:
            cols = self.db_connection.execute(f"PRAGMA table_info({t});").fetchall()
            col_desc = [f"{c[1]} ({c[2]})" for c in cols]
            parts.append(f"Table '{t}': {', '.join(col_desc)}")
        return "\n".join(parts)

    def _get_error(self, query: Optional[str]) -> Optional[str]:
        if not query:
            return None
        try:
            self.db_connection.execute(query)
            return None
        except sqlite3.Error as e:
            return str(e)

    def close(self):
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None