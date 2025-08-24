use anyhow::{Context, Result};
use fantoccini::{ClientBuilder, Locator};
use shared::{TestAction, ActionType};
use crate::models::{BrowserSession, ExecutionConfig};
use tokio::time::{sleep, Duration};
use tracing::{debug, warn, info};
use serde_json::json;
use uuid::Uuid;
use chrono::Utc;
use base64::{Engine, engine::general_purpose};

#[derive(Clone)]
pub struct BrowserController {
    webdriver_url: String,
    config: ExecutionConfig,
}

impl BrowserController {
    pub async fn new(config: ExecutionConfig) -> Result<Self> {
        info!("Initializing Browser Controller for test execution...");
        
        let webdriver_url = std::env::var("WEBDRIVER_URL")
            .unwrap_or_else(|_| "http://localhost:4444".to_string());
        
        // Test WebDriver connection
        match Self::test_webdriver_connection(&webdriver_url).await {
            Ok(_) => {
                info!("WebDriver connection successful at {}", webdriver_url);
            }
            Err(e) => {
                warn!("WebDriver not available at {}: {}", webdriver_url, e);
                info!("To use browser automation for tests:");
                info!("1. Install Chrome/Chromium");
                info!("2. Download ChromeDriver from https://chromedriver.chromium.org/");
                info!("3. Run: chromedriver --port=4444");
                info!("4. Set WEBDRIVER_URL=http://localhost:4444");
            }
        }
        
        Ok(Self { webdriver_url, config })
    }

    async fn test_webdriver_connection(url: &str) -> Result<()> {
        let client = reqwest::Client::new();
        let response = client
            .get(&format!("{}/status", url))
            .timeout(Duration::from_secs(5))
            .send()
            .await
            .context("Failed to connect to WebDriver")?;
            
        if response.status().is_success() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("WebDriver returned status: {}", response.status()))
        }
    }

    pub async fn create_session(&self, url: &str) -> Result<BrowserSession> {
        debug!("Creating browser session for URL: {}", url);
        
        let session = BrowserSession {
            id: Uuid::new_v4(),
            url: url.to_string(),
            viewport_width: self.config.viewport.0,
            viewport_height: self.config.viewport.1,
            user_agent: None,
            created_at: Utc::now(),
        };

        debug!("Browser session created: {}", session.id);
        Ok(session)
    }

    pub async fn execute_action(
        &self,
        client: &fantoccini::Client,
        action: &TestAction,
    ) -> Result<String> {
        debug!("Executing action: {:?} on target: {}", action.action_type, action.target);

        let result = match action.action_type {
            ActionType::Navigate => {
                if let Some(url) = &action.value {
                    client.goto(url).await.context("Failed to navigate")?;
                    format!("Navigated to: {}", url)
                } else {
                    return Err(anyhow::anyhow!("Navigate action requires a URL value"));
                }
            }
            ActionType::Click => {
                let element = self.find_element(client, &action.target).await?;
                element.click().await.context("Failed to click element")?;
                format!("Clicked element: {}", action.target)
            }
            ActionType::Type => {
                if let Some(text) = &action.value {
                    let element = self.find_element(client, &action.target).await?;
                    element.clear().await.context("Failed to clear element")?;
                    element.send_keys(text).await.context("Failed to type text")?;
                    format!("Typed '{}' into element: {}", text, action.target)
                } else {
                    return Err(anyhow::anyhow!("Type action requires a text value"));
                }
            }
            ActionType::Wait => {
                let wait_time = action.value
                    .as_ref()
                    .and_then(|v| v.parse::<u64>().ok())
                    .unwrap_or(1000);
                sleep(Duration::from_millis(wait_time)).await;
                format!("Waited for {}ms", wait_time)
            }
            ActionType::Screenshot => {
                let screenshot_data = client
                    .screenshot()
                    .await
                    .context("Failed to capture screenshot")?;
                
                // In a real implementation, you'd save this to storage
                format!("Captured screenshot ({} bytes)", screenshot_data.len())
            }
            ActionType::Scroll => {
                if let Some(script_value) = &action.value {
                    let script = match script_value.as_str() {
                        "top" => "window.scrollTo(0, 0);",
                        "bottom" => "window.scrollTo(0, document.body.scrollHeight);",
                        _ => script_value, // Custom JavaScript
                    };
                    
                    client.execute(script, vec![]).await
                        .context("Failed to execute scroll script")?;
                    format!("Scrolled: {}", script_value)
                } else {
                    // Default scroll to element using JavaScript selector
                    let script = format!(
                        "document.querySelector('{}').scrollIntoView();",
                        action.target.replace("'", "\\'")
                    );
                    client.execute(&script, vec![]).await.context("Failed to scroll to element")?;
                    format!("Scrolled to element: {}", action.target)
                }
            }
        };

        // Wait after action if specified
        if let Some(wait_time) = action.wait_after_ms {
            debug!("Waiting {}ms after action", wait_time);
            sleep(Duration::from_millis(wait_time)).await;
        } else {
            // Default wait after action
            sleep(Duration::from_millis(self.config.wait_after_action_ms)).await;
        }

        Ok(result)
    }

    async fn find_element(
        &self,
        client: &fantoccini::Client,
        selector: &str,
    ) -> Result<fantoccini::elements::Element> {
        debug!("Finding element with selector: {}", selector);

        // Try different selector types
        let locator = if selector.starts_with("//") {
            Locator::XPath(selector)
        } else if selector.starts_with("#") {
            Locator::Id(&selector[1..])
        } else if selector.starts_with(".") {
            Locator::Css(selector)
        } else {
            Locator::Css(selector)
        };

        // Wait for element to be present
        let element = client
            .wait()
            .at_most(Duration::from_millis(self.config.timeout_ms))
            .for_element(locator)
            .await
            .context(format!("Element not found: {}", selector))?;

        debug!("Element found: {}", selector);
        Ok(element)
    }

    pub async fn start_browser_session(&self) -> Result<fantoccini::Client> {
        debug!("Starting browser session with WebDriver");
        
        // Create WebDriver capabilities
        let mut caps = serde_json::Map::new();
        let mut chrome_args = self.config.browser_args.clone();
        
        if self.config.headless {
            chrome_args.push("--headless".to_string());
        }
        
        chrome_args.push(format!("--window-size={},{}", 
                                self.config.viewport.0, 
                                self.config.viewport.1));

        let chrome_opts = json!({
            "args": chrome_args
        });
        caps.insert("goog:chromeOptions".to_string(), chrome_opts);

        // Connect to WebDriver
        let client = ClientBuilder::native()
            .capabilities(caps)
            .connect(&self.webdriver_url)
            .await
            .context("Failed to connect to WebDriver")?;

        // Set window size
        client
            .set_window_size(self.config.viewport.0, self.config.viewport.1)
            .await
            .context("Failed to set window size")?;

        info!("Browser session started successfully");
        Ok(client)
    }

    pub async fn close_browser_session(&self, client: fantoccini::Client) -> Result<()> {
        debug!("Closing browser session");
        
        if let Err(e) = client.close().await {
            warn!("Failed to close browser session gracefully: {}", e);
        } else {
            debug!("Browser session closed successfully");
        }
        
        Ok(())
    }

    pub async fn get_page_title(&self, client: &fantoccini::Client) -> Result<String> {
        client.title().await.context("Failed to get page title")
    }

    pub async fn get_current_url(&self, client: &fantoccini::Client) -> Result<String> {
        client.current_url().await
            .map(|url| url.to_string())
            .context("Failed to get current URL")
    }

    pub async fn wait_for_page_load(&self, client: &fantoccini::Client) -> Result<()> {
        debug!("Waiting for page to load");
        
        // Wait for document ready state
        let script = r#"
            return document.readyState === 'complete';
        "#;
        
        let mut attempts = 0;
        let max_attempts = (self.config.timeout_ms / 100) as usize;
        
        while attempts < max_attempts {
            match client.execute(script, vec![]).await {
                Ok(result) => {
                    if let Some(ready) = result.as_bool() {
                        if ready {
                            debug!("Page loaded successfully");
                            return Ok(());
                        }
                    }
                }
                Err(_) => {
                    // Continue waiting
                }
            }
            
            sleep(Duration::from_millis(100)).await;
            attempts += 1;
        }
        
        warn!("Page load timeout after {}ms", self.config.timeout_ms);
        Ok(()) // Don't fail completely, just warn
    }

    pub async fn evaluate_javascript(
        &self,
        client: &fantoccini::Client,
        script: &str,
    ) -> Result<serde_json::Value> {
        client.execute(script, vec![]).await
            .context("Failed to execute JavaScript")
    }

    pub async fn take_screenshot(&self, client: &fantoccini::Client) -> Result<Vec<u8>> {
        let screenshot_base64 = client
            .screenshot()
            .await
            .context("Failed to capture screenshot")?;

        let screenshot_data = general_purpose::STANDARD
            .decode(&screenshot_base64)
            .context("Failed to decode base64 screenshot")?;

        Ok(screenshot_data)
    }
}