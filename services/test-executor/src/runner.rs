use anyhow::{Context, Result};
use shared::{TestCase, TestType};
use crate::{
    browser::BrowserController,
    models::{TestExecution, TestResult, TestStatus, ExecutionStatus, AssertionResult, ExecutionConfig}
};
use tokio::time::{Instant, Duration};
use tracing::{debug, info, error, warn};
use uuid::Uuid;
use chrono::Utc;

pub struct TestRunner {
    browser_controller: BrowserController,
    config: ExecutionConfig,
}

impl TestRunner {
    pub async fn new(config: ExecutionConfig) -> Result<Self> {
        let browser_controller = BrowserController::new(config.clone()).await?;
        
        Ok(Self {
            browser_controller,
            config,
        })
    }

    async fn find_element_helper(
        &self,
        client: &fantoccini::Client,
        selector: &str,
    ) -> Result<fantoccini::elements::Element> {
        let locator = if selector.starts_with("//") {
            fantoccini::Locator::XPath(selector)
        } else if selector.starts_with("#") {
            fantoccini::Locator::Id(&selector[1..])
        } else if selector.starts_with(".") {
            fantoccini::Locator::Css(selector)
        } else {
            fantoccini::Locator::Css(selector)
        };

        client
            .wait()
            .at_most(Duration::from_millis(self.config.timeout_ms))
            .for_element(locator)
            .await
            .context(format!("Element not found: {}", selector))
    }

    pub async fn execute_test_suite(
        &self,
        test_suite_id: Uuid,
        url: &str,
        test_cases: Vec<TestCase>,
    ) -> Result<TestExecution> {
        info!("Starting test suite execution: {} with {} tests", test_suite_id, test_cases.len());
        
        let mut execution = TestExecution {
            id: Uuid::new_v4(),
            test_suite_id,
            url: url.to_string(),
            status: ExecutionStatus::Running,
            started_at: Utc::now(),
            completed_at: None,
            total_tests: test_cases.len() as u32,
            passed_tests: 0,
            failed_tests: 0,
            skipped_tests: 0,
            test_results: Vec::new(),
        };

        // Start browser session
        let client = match self.browser_controller.start_browser_session().await {
            Ok(client) => client,
            Err(e) => {
                error!("Failed to start browser session: {}", e);
                execution.status = ExecutionStatus::Failed;
                return Ok(execution);
            }
        };

        // Navigate to the target URL
        if let Err(e) = client.goto(url).await {
            error!("Failed to navigate to {}: {}", url, e);
            execution.status = ExecutionStatus::Failed;
            let _ = self.browser_controller.close_browser_session(client).await;
            return Ok(execution);
        }

        // Wait for initial page load
        if let Err(e) = self.browser_controller.wait_for_page_load(&client).await {
            warn!("Page load timeout: {}", e);
        }

        // Execute each test case
        for test_case in test_cases {
            let test_result = self.execute_test_case(&client, &test_case).await;
            
            match test_result.status {
                TestStatus::Passed => execution.passed_tests += 1,
                TestStatus::Failed | TestStatus::Error => execution.failed_tests += 1,
                TestStatus::Skipped => execution.skipped_tests += 1,
                _ => {}
            }
            
            execution.test_results.push(test_result);
        }

        // Close browser session
        if let Err(e) = self.browser_controller.close_browser_session(client).await {
            warn!("Failed to close browser session: {}", e);
        }

        // Update execution status
        execution.completed_at = Some(Utc::now());
        execution.status = if execution.failed_tests > 0 {
            ExecutionStatus::Failed
        } else {
            ExecutionStatus::Completed
        };

        info!("Test suite execution completed: {}/{} tests passed", 
              execution.passed_tests, execution.total_tests);

        Ok(execution)
    }

    async fn execute_test_case(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> TestResult {
        info!("Executing test case: {}", test_case.name);
        let start_time = Instant::now();
        
        let mut test_result = TestResult {
            id: Uuid::new_v4(),
            test_case_id: test_case.id,
            test_name: test_case.name.clone(),
            status: TestStatus::Running,
            started_at: Utc::now(),
            completed_at: None,
            duration_ms: None,
            error_message: None,
            screenshot_path: None,
            logs: vec![format!("Starting test: {}", test_case.name)],
            assertions: Vec::new(),
        };

        // Execute pre-test actions
        for action in &test_case.actions {
            match self.browser_controller.execute_action(client, action).await {
                Ok(result) => {
                    test_result.logs.push(format!("Action completed: {}", result));
                    debug!("Action executed successfully: {:?}", action.action_type);
                }
                Err(e) => {
                    let error_msg = format!("Action failed: {:?} - {}", action.action_type, e);
                    error!("{}", error_msg);
                    test_result.error_message = Some(error_msg.clone());
                    test_result.logs.push(error_msg);
                    test_result.status = TestStatus::Error;
                    
                    // Take screenshot on failure
                    if self.config.screenshot_on_failure {
                        if let Ok(_screenshot) = self.browser_controller.take_screenshot(client).await {
                            test_result.screenshot_path = Some(format!("failure_{}.png", test_result.id));
                            test_result.logs.push("Screenshot captured on failure".to_string());
                        }
                    }
                    
                    test_result.completed_at = Some(Utc::now());
                    test_result.duration_ms = Some(start_time.elapsed().as_millis() as u64);
                    return test_result;
                }
            }
        }

        // Execute the main test assertion
        let assertion_result = self.execute_test_assertion(client, test_case).await;
        
        match assertion_result {
            Ok(assertion) => {
                test_result.assertions.push(assertion.clone());
                test_result.status = if assertion.passed {
                    TestStatus::Passed
                } else {
                    TestStatus::Failed
                };
                test_result.logs.push(format!("Assertion: {}", assertion.message));
            }
            Err(e) => {
                let error_msg = format!("Test assertion failed: {}", e);
                error!("{}", error_msg);
                test_result.error_message = Some(error_msg.clone());
                test_result.logs.push(error_msg);
                test_result.status = TestStatus::Error;
                
                // Take screenshot on failure
                if self.config.screenshot_on_failure {
                    if let Ok(_screenshot) = self.browser_controller.take_screenshot(client).await {
                        test_result.screenshot_path = Some(format!("failure_{}.png", test_result.id));
                        test_result.logs.push("Screenshot captured on failure".to_string());
                    }
                }
            }
        }

        test_result.completed_at = Some(Utc::now());
        test_result.duration_ms = Some(start_time.elapsed().as_millis() as u64);

        info!("Test case completed: {} - {:?}", test_case.name, test_result.status);
        test_result
    }

    async fn execute_test_assertion(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        debug!("Executing assertion for test type: {:?}", test_case.test_type);

        match test_case.test_type {
            TestType::ElementExists => {
                self.assert_element_exists(client, test_case).await
            }
            TestType::ElementVisible => {
                self.assert_element_visible(client, test_case).await
            }
            TestType::ElementText => {
                self.assert_element_text(client, test_case).await
            }
            TestType::ElementAttribute => {
                self.assert_element_attribute(client, test_case).await
            }
            TestType::PageTitle => {
                self.assert_page_title(client, test_case).await
            }
            TestType::FormSubmission => {
                self.assert_form_submission(client, test_case).await
            }
            TestType::Navigation => {
                self.assert_navigation(client, test_case).await
            }
            TestType::VisualRegression => {
                // This would integrate with the visual engine service
                self.assert_visual_regression(client, test_case).await
            }
        }
    }

    async fn assert_element_exists(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        let target = test_case.target_element.as_ref()
            .ok_or_else(|| anyhow::anyhow!("ElementExists test requires target_element"))?;

        match self.find_element_helper(client, target).await {
            Ok(_) => Ok(AssertionResult {
                assertion_type: "ElementExists".to_string(),
                expected: format!("Element '{}' should exist", target),
                actual: "Element found".to_string(),
                passed: true,
                message: format!("Element '{}' exists on the page", target),
            }),
            Err(e) => Ok(AssertionResult {
                assertion_type: "ElementExists".to_string(),
                expected: format!("Element '{}' should exist", target),
                actual: format!("Element not found: {}", e),
                passed: false,
                message: format!("Element '{}' does not exist on the page", target),
            }),
        }
    }

    async fn assert_element_visible(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        let target = test_case.target_element.as_ref()
            .ok_or_else(|| anyhow::anyhow!("ElementVisible test requires target_element"))?;

        match self.find_element_helper(client, target).await {
            Ok(element) => {
                // Check if element is displayed
                let is_displayed = element.is_displayed().await.unwrap_or(false);
                
                Ok(AssertionResult {
                    assertion_type: "ElementVisible".to_string(),
                    expected: format!("Element '{}' should be visible", target),
                    actual: format!("Element visibility: {}", is_displayed),
                    passed: is_displayed,
                    message: if is_displayed {
                        format!("Element '{}' is visible", target)
                    } else {
                        format!("Element '{}' is not visible", target)
                    },
                })
            }
            Err(e) => Ok(AssertionResult {
                assertion_type: "ElementVisible".to_string(),
                expected: format!("Element '{}' should be visible", target),
                actual: format!("Element not found: {}", e),
                passed: false,
                message: format!("Element '{}' not found, cannot check visibility", target),
            }),
        }
    }

    async fn assert_element_text(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        let target = test_case.target_element.as_ref()
            .ok_or_else(|| anyhow::anyhow!("ElementText test requires target_element"))?;
        let expected_text = test_case.expected_value.as_ref()
            .ok_or_else(|| anyhow::anyhow!("ElementText test requires expected_value"))?;

        match self.find_element_helper(client, target).await {
            Ok(element) => {
                let actual_text = element.text().await.unwrap_or_default();
                let passed = actual_text.trim() == expected_text.trim();
                
                Ok(AssertionResult {
                    assertion_type: "ElementText".to_string(),
                    expected: expected_text.clone(),
                    actual: actual_text.clone(),
                    passed,
                    message: if passed {
                        format!("Element '{}' has expected text: '{}'", target, expected_text)
                    } else {
                        format!("Element '{}' text mismatch. Expected: '{}', Actual: '{}'", 
                               target, expected_text, actual_text)
                    },
                })
            }
            Err(e) => Ok(AssertionResult {
                assertion_type: "ElementText".to_string(),
                expected: expected_text.clone(),
                actual: format!("Element not found: {}", e),
                passed: false,
                message: format!("Element '{}' not found, cannot check text", target),
            }),
        }
    }

    async fn assert_element_attribute(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        let target = test_case.target_element.as_ref()
            .ok_or_else(|| anyhow::anyhow!("ElementAttribute test requires target_element"))?;
        let expected_value = test_case.expected_value.as_ref()
            .ok_or_else(|| anyhow::anyhow!("ElementAttribute test requires expected_value in format 'attribute=value'"))?;

        // Parse expected value (format: "attribute=value")
        let parts: Vec<&str> = expected_value.splitn(2, '=').collect();
        if parts.len() != 2 {
            return Err(anyhow::anyhow!("ElementAttribute expected_value must be in format 'attribute=value'"));
        }
        let (attr_name, expected_attr_value) = (parts[0], parts[1]);

        match self.find_element_helper(client, target).await {
            Ok(element) => {
                let actual_attr_value = element.attr(attr_name).await.unwrap_or_default();
                let actual_attr_value_str = actual_attr_value.clone().unwrap_or_default();
                let passed = actual_attr_value.as_deref() == Some(expected_attr_value);
                
                Ok(AssertionResult {
                    assertion_type: "ElementAttribute".to_string(),
                    expected: expected_value.clone(),
                    actual: format!("{}={}", attr_name, actual_attr_value_str),
                    passed,
                    message: if passed {
                        format!("Element '{}' has expected attribute {}='{}'", target, attr_name, expected_attr_value)
                    } else {
                        format!("Element '{}' attribute mismatch. Expected: {}='{}', Actual: {}='{}'", 
                               target, attr_name, expected_attr_value, attr_name, actual_attr_value_str)
                    },
                })
            }
            Err(e) => Ok(AssertionResult {
                assertion_type: "ElementAttribute".to_string(),
                expected: expected_value.clone(),
                actual: format!("Element not found: {}", e),
                passed: false,
                message: format!("Element '{}' not found, cannot check attribute", target),
            }),
        }
    }

    async fn assert_page_title(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        let expected_title = test_case.expected_value.as_ref()
            .ok_or_else(|| anyhow::anyhow!("PageTitle test requires expected_value"))?;

        match self.browser_controller.get_page_title(client).await {
            Ok(actual_title) => {
                let passed = actual_title.trim() == expected_title.trim();
                
                Ok(AssertionResult {
                    assertion_type: "PageTitle".to_string(),
                    expected: expected_title.clone(),
                    actual: actual_title.clone(),
                    passed,
                    message: if passed {
                        format!("Page title matches expected: '{}'", expected_title)
                    } else {
                        format!("Page title mismatch. Expected: '{}', Actual: '{}'", 
                               expected_title, actual_title)
                    },
                })
            }
            Err(e) => Ok(AssertionResult {
                assertion_type: "PageTitle".to_string(),
                expected: expected_title.clone(),
                actual: format!("Failed to get title: {}", e),
                passed: false,
                message: format!("Could not retrieve page title: {}", e),
            }),
        }
    }

    async fn assert_form_submission(
        &self,
        _client: &fantoccini::Client,
        _test_case: &TestCase,
    ) -> Result<AssertionResult> {
        // This is a placeholder for form submission testing
        // In a real implementation, you'd need to handle form data and submission logic
        
        Ok(AssertionResult {
            assertion_type: "FormSubmission".to_string(),
            expected: "Form submission successful".to_string(),
            actual: "Form submission test not fully implemented".to_string(),
            passed: false,
            message: "Form submission testing requires custom implementation".to_string(),
        })
    }

    async fn assert_navigation(
        &self,
        client: &fantoccini::Client,
        test_case: &TestCase,
    ) -> Result<AssertionResult> {
        let expected_url = test_case.expected_value.as_ref()
            .ok_or_else(|| anyhow::anyhow!("Navigation test requires expected_value (target URL)"))?;

        match self.browser_controller.get_current_url(client).await {
            Ok(current_url) => {
                let passed = current_url == *expected_url;
                
                Ok(AssertionResult {
                    assertion_type: "Navigation".to_string(),
                    expected: expected_url.clone(),
                    actual: current_url.clone(),
                    passed,
                    message: if passed {
                        format!("Successfully navigated to: '{}'", expected_url)
                    } else {
                        format!("Navigation mismatch. Expected: '{}', Actual: '{}'", 
                               expected_url, current_url)
                    },
                })
            }
            Err(e) => Ok(AssertionResult {
                assertion_type: "Navigation".to_string(),
                expected: expected_url.clone(),
                actual: format!("Failed to get current URL: {}", e),
                passed: false,
                message: format!("Could not verify navigation: {}", e),
            }),
        }
    }

    async fn assert_visual_regression(
        &self,
        _client: &fantoccini::Client,
        _test_case: &TestCase,
    ) -> Result<AssertionResult> {
        // This would integrate with the visual engine service to compare screenshots
        // For now, it's a placeholder
        
        Ok(AssertionResult {
            assertion_type: "VisualRegression".to_string(),
            expected: "Visual regression test passed".to_string(),
            actual: "Visual regression testing requires visual engine integration".to_string(),
            passed: false,
            message: "Visual regression testing not yet integrated with visual engine".to_string(),
        })
    }
}