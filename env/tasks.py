# env/tasks.py
# Each task is a SQL debugging puzzle.
# We use SQLite (built into Python — no installation needed!).
# Each task has: setup SQL (creates tables + data), a broken query, and the expected answer.

TASKS = {

    # ─────────────────────────────────────────────
    # TASK 1: EASY — Fix a syntax error
    # The bug: missing comma between column names
    # A beginner SQL mistake
    # ─────────────────────────────────────────────
    "task_syntax": {
        "name": "Fix syntax error",
        "difficulty": "easy",
        "max_steps": 3,
        "description": (
            "Fix the SQL syntax error. The query is supposed to return "
            "the name and salary of all employees earning over 50000."
        ),
        "hint": "Look carefully at the SELECT clause — something is missing between column names.",

        # This SQL runs first to create the database
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

        # This is the BROKEN query the agent must fix
        # Bug: "name salary" should be "name, salary"
        "broken_query": "SELECT name salary FROM employees WHERE salary > 50000;",

        # This is the CORRECT query (used by the grader to get expected output)
        "correct_query": "SELECT name, salary FROM employees WHERE salary > 50000;",

        # Expected result metadata
        "expected_columns": ["name", "salary"],
        "expected_row_count": 3,  # Alice, Carol, Dave
    },

    # ─────────────────────────────────────────────
    # TASK 2: MEDIUM — Fix a logic bug
    # The bug: uses LEFT JOIN when INNER JOIN is needed,
    # causing NULL rows to appear in results
    # ─────────────────────────────────────────────
    "task_logic": {
        "name": "Fix logic bug",
        "difficulty": "medium",
        "max_steps": 5,
        "description": (
            "This query is supposed to return only orders that have a matching customer. "
            "But it's returning orders with NULL customer names too. Fix it."
        ),
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

        # Bug: LEFT JOIN includes order with customer_id=99 (no matching customer)
        "broken_query": """
            SELECT customers.name, orders.product, orders.amount
            FROM orders
            LEFT JOIN customers ON orders.customer_id = customers.id;
        """,

        "correct_query": """
            SELECT customers.name, orders.product, orders.amount
            FROM orders
            INNER JOIN customers ON orders.customer_id = customers.id;
        """,

        "expected_columns": ["name", "product", "amount"],
        "expected_row_count": 2,  # only Alice and Bob's orders
    },

    # ─────────────────────────────────────────────
    # TASK 3: HARD — Fix a NULL handling + aggregation bug
    # The bug: AVG() ignores NULLs but COUNT(*) counts them,
    # causing a misleading average. Agent must use COALESCE.
    # This genuinely challenges frontier models.
    # ─────────────────────────────────────────────
    "task_advanced": {
        "name": "Fix NULL and aggregation bug",
        "difficulty": "hard",
        "max_steps": 7,
        "description": (
            "This query calculates average bonus per department. "
            "Some employees have NULL bonus (no bonus given). "
            "The query should treat NULL bonus as 0 when computing the average, "
            "but currently it ignores NULLs entirely, giving a misleadingly high average. "
            "Fix it so NULL bonuses are counted as 0."
        ),
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

        # Bug: AVG(bonus) skips NULLs — Engineering avg = (5000+3000)/2 = 4000, not (5000+0+3000)/3 = 2666
        "broken_query": """
            SELECT department, AVG(bonus) as avg_bonus
            FROM staff
            GROUP BY department
            ORDER BY department;
        """,

        # Fix: COALESCE(bonus, 0) replaces NULL with 0 before averaging
        "correct_query": """
            SELECT department, AVG(COALESCE(bonus, 0)) as avg_bonus
            FROM staff
            GROUP BY department
            ORDER BY department;
        """,

        "expected_columns": ["department", "avg_bonus"],
        "expected_row_count": 2,  # Engineering and HR
    },

    # ─────────────────────────────────────────────
    # TASK 4: EASY-MEDIUM — Fix wrong comparison operator
    # The bug: uses > instead of >= missing boundary value
    # ─────────────────────────────────────────────
    "task_boundary": {
        "name": "Fix boundary condition bug",
        "difficulty": "easy",
        "max_steps": 3,
        "description": (
            "Fix the SQL query. It should return all products with "
            "stock of 100 or more, but it's missing products with exactly 100 stock."
        ),
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

        # Bug: > 100 misses the product with exactly 100 stock
        "broken_query": "SELECT name, stock FROM products WHERE stock > 100;",

        "correct_query": "SELECT name, stock FROM products WHERE stock >= 100;",

        "expected_columns": ["name", "stock"],
        "expected_row_count": 3,  # Laptop, Phone, Headphones
    },

    # ─────────────────────────────────────────────
    # TASK 5: MEDIUM — Fix missing GROUP BY
    # The bug: uses COUNT() with another column but forgets GROUP BY
    # ─────────────────────────────────────────────
    "task_groupby": {
        "name": "Fix missing GROUP BY",
        "difficulty": "medium",
        "max_steps": 5,
        "description": (
            "This query tries to count how many orders each customer has made. "
            "But it's missing a GROUP BY clause, so it returns wrong results. Fix it."
        ),
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

        # Bug: missing GROUP BY customers2.name
        "broken_query": """
            SELECT customers2.name, COUNT(orders2.id) as order_count
            FROM customers2
            INNER JOIN orders2 ON customers2.id = orders2.customer_id;
        """,

        "correct_query": """
            SELECT customers2.name, COUNT(orders2.id) as order_count
            FROM customers2
            INNER JOIN orders2 ON customers2.id = orders2.customer_id
            GROUP BY customers2.name
            ORDER BY customers2.name;
        """,

        "expected_columns": ["name", "order_count"],
        "expected_row_count": 3,  # Alice:2, Bob:1, Carol:3
    },

    # ─────────────────────────────────────────────
    # TASK 6: HARD — Fix wrong HAVING clause
    # The bug: uses WHERE instead of HAVING for aggregate filter
    # This is a very common mistake even for experienced developers
    # ─────────────────────────────────────────────
    "task_having": {
        "name": "Fix WHERE vs HAVING bug",
        "difficulty": "hard",
        "max_steps": 7,
        "description": (
            "This query tries to find departments where the average salary "
            "is greater than 60000. But it uses WHERE instead of HAVING "
            "for the aggregate condition, causing a SQL error. Fix it."
        ),
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

        # Bug: WHERE AVG(salary) > 60000 is invalid — must use HAVING
        "broken_query": """
            SELECT department, AVG(salary) as avg_salary
            FROM staff2
            GROUP BY department
            WHERE AVG(salary) > 60000;
        """,

        "correct_query": """
            SELECT department, AVG(salary) as avg_salary
            FROM staff2
            GROUP BY department
            HAVING AVG(salary) > 60000
            ORDER BY department;
        """,

        "expected_columns": ["department", "avg_salary"],
        "expected_row_count": 1,  # Only Engineering qualifies
    },
}