-- SQA-AI Database Schema
-- SQLite database for storing analysis results

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================
-- PROJECTS TABLE
-- Stores information about analyzed projects
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    description TEXT,
    language TEXT DEFAULT 'python',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    
    UNIQUE(path)
);

CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);
CREATE INDEX IF NOT EXISTS idx_projects_path ON projects(path);


-- ============================================
-- ANALYSES TABLE (moved before metrics/ddi for FK)
-- Stores analysis runs (project-level)
-- ============================================
CREATE TABLE IF NOT EXISTS analyses (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    
    -- Summary metrics
    total_files INTEGER DEFAULT 0,
    total_sloc INTEGER DEFAULT 0,
    avg_maintainability_index REAL DEFAULT 0.0,
    avg_complexity REAL DEFAULT 0.0,
    avg_ddi_score REAL DEFAULT 0.0,
    
    -- Health
    overall_health_score REAL DEFAULT 100.0,
    overall_status TEXT DEFAULT 'good',
    
    -- Counts
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    
    -- Metadata
    analyzer_version TEXT DEFAULT '1.0.0',
    run_duration_seconds REAL DEFAULT 0.0,
    notes TEXT,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analyses_project ON analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_date ON analyses(run_at);


-- ============================================
-- FILES TABLE
-- Stores information about analyzed files
-- ============================================
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    path TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    language TEXT DEFAULT 'python',
    content_hash TEXT,
    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, relative_path)
);

CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(relative_path);
CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash);


-- ============================================
-- METRICS TABLE
-- Stores code metrics for each file scan
-- ============================================
CREATE TABLE IF NOT EXISTS metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    analysis_id INTEGER,
    
    -- Size metrics
    loc INTEGER DEFAULT 0,
    sloc INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    comment_density REAL DEFAULT 0.0,
    
    -- Complexity metrics
    cyclomatic_complexity REAL DEFAULT 0.0,
    max_complexity INTEGER DEFAULT 0,
    avg_complexity REAL DEFAULT 0.0,
    complexity_rank TEXT DEFAULT 'A',
    
    -- Maintainability
    maintainability_index REAL DEFAULT 100.0,
    mi_rank TEXT DEFAULT 'A',
    
    -- Halstead metrics
    halstead_volume REAL DEFAULT 0.0,
    halstead_difficulty REAL DEFAULT 0.0,
    halstead_effort REAL DEFAULT 0.0,
    halstead_bugs REAL DEFAULT 0.0,
    
    -- Structure metrics
    function_count INTEGER DEFAULT 0,
    class_count INTEGER DEFAULT 0,
    import_count INTEGER DEFAULT 0,
    avg_function_length REAL DEFAULT 0.0,
    max_function_length INTEGER DEFAULT 0,
    
    -- Documentation
    docstring_coverage REAL DEFAULT 0.0,
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_metrics_file ON metrics(file_id);
CREATE INDEX IF NOT EXISTS idx_metrics_analysis ON metrics(analysis_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(computed_at);


-- ============================================
-- DDI TABLE
-- Stores DDI calculations for each file
-- ============================================
CREATE TABLE IF NOT EXISTS ddi_records (
    ddi_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    analysis_id INTEGER,
    
    -- DDI Score
    ddi_score REAL DEFAULT 0.0,
    risk_level TEXT DEFAULT 'low',
    
    -- Component scores
    decay_rate_score REAL DEFAULT 0.0,
    entropy_score REAL DEFAULT 0.0,
    volatility_score REAL DEFAULT 0.0,
    frequency_score REAL DEFAULT 0.0,
    
    -- Raw values
    decay_rate REAL DEFAULT 0.0,
    contributor_entropy REAL DEFAULT 0.0,
    volatility REAL DEFAULT 0.0,
    commit_frequency REAL DEFAULT 0.0,
    
    -- Context
    contributor_count INTEGER DEFAULT 0,
    total_commits INTEGER DEFAULT 0,
    age_days INTEGER DEFAULT 0,
    days_since_last_change INTEGER DEFAULT 0,
    
    -- Prediction
    confidence REAL DEFAULT 0.0,
    predicted_issue_probability REAL DEFAULT 0.0,
    recommended_action TEXT,
    
    -- Metadata
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE,
    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_ddi_file ON ddi_records(file_id);
CREATE INDEX IF NOT EXISTS idx_ddi_score ON ddi_records(ddi_score);
CREATE INDEX IF NOT EXISTS idx_ddi_risk ON ddi_records(risk_level);


-- ============================================
-- RECOMMENDATIONS TABLE
-- Stores recommendations from each analysis
-- ============================================
CREATE TABLE IF NOT EXISTS recommendations (
    rec_id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    file_id INTEGER,
    
    -- Recommendation details
    title TEXT NOT NULL,
    message TEXT,
    severity TEXT DEFAULT 'medium',
    category TEXT DEFAULT 'general',
    
    -- Context
    metric_name TEXT,
    metric_value REAL,
    threshold REAL,
    
    -- Action
    action TEXT,
    effort_estimate TEXT DEFAULT 'medium',
    impact TEXT DEFAULT 'medium',
    priority_score REAL DEFAULT 0.0,
    
    -- Location
    line_start INTEGER,
    line_end INTEGER,
    function_name TEXT,
    class_name TEXT,
    
    -- Status tracking
    status TEXT DEFAULT 'open',
    resolved_at TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (analysis_id) REFERENCES analyses(analysis_id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_rec_analysis ON recommendations(analysis_id);
CREATE INDEX IF NOT EXISTS idx_rec_file ON recommendations(file_id);
CREATE INDEX IF NOT EXISTS idx_rec_severity ON recommendations(severity);
CREATE INDEX IF NOT EXISTS idx_rec_status ON recommendations(status);


-- ============================================
-- METRIC HISTORY TABLE
-- Stores historical metric snapshots for trend analysis
-- ============================================
CREATE TABLE IF NOT EXISTS metric_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    
    -- Key metrics to track over time
    maintainability_index REAL,
    cyclomatic_complexity REAL,
    sloc INTEGER,
    comment_density REAL,
    ddi_score REAL,
    
    -- Snapshot timestamp
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (file_id) REFERENCES files(file_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_history_file ON metric_history(file_id);
CREATE INDEX IF NOT EXISTS idx_history_date ON metric_history(snapshot_at);


-- ============================================
-- CONTRIBUTORS TABLE
-- Stores contributor information from git
-- ============================================
CREATE TABLE IF NOT EXISTS contributors (
    contributor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    
    name TEXT NOT NULL,
    email TEXT,
    
    -- Statistics
    commit_count INTEGER DEFAULT 0,
    files_touched INTEGER DEFAULT 0,
    total_insertions INTEGER DEFAULT 0,
    total_deletions INTEGER DEFAULT 0,
    
    -- Activity
    first_commit_date TIMESTAMP,
    last_commit_date TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    UNIQUE(project_id, email)
);

CREATE INDEX IF NOT EXISTS idx_contrib_project ON contributors(project_id);


-- ============================================
-- SETTINGS TABLE
-- Stores user preferences and configuration
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('theme', 'light', 'Dashboard theme'),
    ('default_language', 'python', 'Default language for analysis'),
    ('max_files_display', '50', 'Maximum files to show in dashboard'),
    ('enable_git_analysis', 'true', 'Enable git history analysis'),
    ('ddi_weight_decay', '0.35', 'DDI weight for decay rate'),
    ('ddi_weight_entropy', '0.30', 'DDI weight for entropy'),
    ('ddi_weight_volatility', '0.20', 'DDI weight for volatility'),
    ('ddi_weight_frequency', '0.15', 'DDI weight for frequency');


-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View: Latest metrics per file
CREATE VIEW IF NOT EXISTS v_latest_metrics AS
SELECT 
    f.file_id,
    f.relative_path,
    f.filename,
    p.name as project_name,
    m.metric_id,
    m.loc,
    m.sloc,
    m.cyclomatic_complexity,
    m.maintainability_index,
    m.mi_rank,
    m.function_count,
    m.class_count,
    m.computed_at
FROM files f
JOIN projects p ON f.project_id = p.project_id
LEFT JOIN metrics m ON f.file_id = m.file_id
WHERE m.metric_id IS NULL OR m.metric_id = (
    SELECT MAX(m2.metric_id) 
    FROM metrics m2 
    WHERE m2.file_id = f.file_id
);

-- View: Latest DDI per file
CREATE VIEW IF NOT EXISTS v_latest_ddi AS
SELECT 
    f.file_id,
    f.relative_path,
    f.filename,
    p.name as project_name,
    d.ddi_id,
    d.ddi_score,
    d.risk_level,
    d.contributor_count,
    d.total_commits,
    d.confidence,
    d.predicted_issue_probability,
    d.recommended_action,
    d.computed_at
FROM files f
JOIN projects p ON f.project_id = p.project_id
LEFT JOIN ddi_records d ON f.file_id = d.file_id
WHERE d.ddi_id IS NULL OR d.ddi_id = (
    SELECT MAX(d2.ddi_id) 
    FROM ddi_records d2 
    WHERE d2.file_id = f.file_id
);

-- View: Project summary
CREATE VIEW IF NOT EXISTS v_project_summary AS
SELECT 
    p.project_id,
    p.name,
    p.path,
    p.language,
    p.created_at,
    COUNT(DISTINCT f.file_id) as file_count,
    (SELECT MAX(a.run_at) FROM analyses a WHERE a.project_id = p.project_id) as last_analysis,
    (SELECT AVG(m.maintainability_index) FROM metrics m 
     JOIN files f2 ON m.file_id = f2.file_id 
     WHERE f2.project_id = p.project_id) as avg_mi,
    (SELECT AVG(d.ddi_score) FROM ddi_records d 
     JOIN files f3 ON d.file_id = f3.file_id 
     WHERE f3.project_id = p.project_id) as avg_ddi
FROM projects p
LEFT JOIN files f ON p.project_id = f.project_id AND f.is_active = 1
WHERE p.is_active = 1
GROUP BY p.project_id;

-- View: High risk files
CREATE VIEW IF NOT EXISTS v_high_risk_files AS
SELECT 
    f.file_id,
    f.relative_path,
    f.filename,
    p.name as project_name,
    p.project_id,
    d.ddi_score,
    d.risk_level,
    d.predicted_issue_probability,
    d.recommended_action
FROM files f
JOIN projects p ON f.project_id = p.project_id
JOIN ddi_records d ON f.file_id = d.file_id
WHERE d.risk_level IN ('high', 'critical')
AND d.ddi_id = (
    SELECT MAX(d2.ddi_id) 
    FROM ddi_records d2 
    WHERE d2.file_id = f.file_id
)
ORDER BY d.ddi_score DESC;