TableSQL = '''
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    wire_api TEXT NOT NULL,
    env_key TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id TEXT NOT NULL,
    model TEXT NOT NULL UNIQUE,
    sandbox TEXT NOT NULL,
    reasoning_effort TEXT NOT NULL,
    context_window INTEGER,
    tool_output_token_limit INTEGER,
    FOREIGN KEY (provider_id) REFERENCES providers(id)
);

CREATE TABLE IF NOT EXISTS architects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT NOT NULL UNIQUE,
    reasoning_effort TEXT NOT NULL,
    sandbox TEXT NOT NULL,
    forced_login_method TEXT NOT NULL,
    approval_policy TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'executor',
    status TEXT NOT NULL DEFAULT 'UNAVAILABLE',
    FOREIGN KEY (model_id) REFERENCES models(id)
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    project_root TEXT NOT NULL,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CREATED',
    plan_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    architect_id INTEGER,
    worker_id INTEGER,
    status TEXT NOT NULL DEFAULT 'PENDING',
    content_path TEXT,
    context_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id),
    FOREIGN KEY (architect_id) REFERENCES architects(id),
    FOREIGN KEY (worker_id) REFERENCES workers(id),
    UNIQUE (run_id, sequence)
);

CREATE TABLE IF NOT EXISTS executions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    model_id INTEGER,
    sandbox TEXT NOT NULL,
    model TEXT NOT NULL,
    reasoning_effort TEXT NOT NULL,
    context_window INTEGER,
    tool_output_token_limit INTEGER,
    status TEXT NOT NULL DEFAULT 'CREATED',
    exit_code INTEGER,
    summary TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (model_id) REFERENCES models(id)
);

DROP TABLE IF EXISTS events;

CREATE TABLE IF NOT EXISTS orchestration_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
'''
