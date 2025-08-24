use anyhow::{Context, Result};
use crate::{
    runner::TestRunner,
    models::{TestSuite, TestExecution, ExecutionConfig}
};
use tracing::info;
use uuid::Uuid;

#[derive(Clone)]
pub struct TestExecutor {
    config: ExecutionConfig,
}

impl TestExecutor {
    pub fn new(config: ExecutionConfig) -> Self {
        Self { config }
    }

    pub async fn execute_test_suite(&self, test_suite: TestSuite) -> Result<TestExecution> {
        info!("Executing test suite: {} ({})", test_suite.name, test_suite.id);
        
        let runner = TestRunner::new(self.config.clone()).await
            .context("Failed to create test runner")?;

        let execution = runner.execute_test_suite(
            test_suite.id,
            &test_suite.url,
            test_suite.test_cases,
        ).await.context("Failed to execute test suite")?;

        info!("Test suite execution completed: {} - {:?}", 
              test_suite.name, execution.status);

        Ok(execution)
    }

    pub async fn execute_test_by_id(&self, _test_suite_id: Uuid) -> Result<TestExecution> {
        // In a real implementation, this would load the test suite from database
        // For now, return an error
        Err(anyhow::anyhow!("Test suite loading from database not implemented"))
    }

    pub fn get_config(&self) -> &ExecutionConfig {
        &self.config
    }

    pub fn update_config(&mut self, config: ExecutionConfig) {
        self.config = config;
    }
}