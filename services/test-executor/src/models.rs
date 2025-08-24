use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use shared::TestCase;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestSuite {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub url: String,
    pub test_cases: Vec<TestCase>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestExecution {
    pub id: Uuid,
    pub test_suite_id: Uuid,
    pub url: String,
    pub status: ExecutionStatus,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub total_tests: u32,
    pub passed_tests: u32,
    pub failed_tests: u32,
    pub skipped_tests: u32,
    pub test_results: Vec<TestResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ExecutionStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Cancelled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestResult {
    pub id: Uuid,
    pub test_case_id: Uuid,
    pub test_name: String,
    pub status: TestStatus,
    pub started_at: DateTime<Utc>,
    pub completed_at: Option<DateTime<Utc>>,
    pub duration_ms: Option<u64>,
    pub error_message: Option<String>,
    pub screenshot_path: Option<String>,
    pub logs: Vec<String>,
    pub assertions: Vec<AssertionResult>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TestStatus {
    Pending,
    Running,
    Passed,
    Failed,
    Skipped,
    Error,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssertionResult {
    pub assertion_type: String,
    pub expected: String,
    pub actual: String,
    pub passed: bool,
    pub message: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BrowserSession {
    pub id: Uuid,
    pub url: String,
    pub viewport_width: u32,
    pub viewport_height: u32,
    pub user_agent: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionConfig {
    pub headless: bool,
    pub viewport: (u32, u32),
    pub timeout_ms: u64,
    pub wait_after_action_ms: u64,
    pub screenshot_on_failure: bool,
    pub browser_args: Vec<String>,
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self {
            headless: true,
            viewport: (1920, 1080),
            timeout_ms: 30000,
            wait_after_action_ms: 500,
            screenshot_on_failure: true,
            browser_args: vec![
                "--no-sandbox".to_string(),
                "--disable-gpu".to_string(),
                "--disable-dev-shm-usage".to_string(),
                "--disable-extensions".to_string(),
                "--disable-web-security".to_string(),
            ],
        }
    }
}