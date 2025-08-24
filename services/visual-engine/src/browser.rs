use anyhow::{Context, Result};
use chromiumoxide::{Browser, BrowserConfig, Page};
use futures_util::StreamExt;
use shared::Viewport;
use tokio::time::{sleep, Duration};
use tracing::{debug, warn, info};
use std::sync::Arc;

pub struct BrowserEngine {
    browser: Arc<Browser>,
}

impl Clone for BrowserEngine {
    fn clone(&self) -> Self {
        Self {
            browser: Arc::clone(&self.browser),
        }
    }
}

impl BrowserEngine {
    pub async fn new() -> Result<Self> {
        info!("Initializing headless Chrome browser...");
        
        let config = BrowserConfig::builder()
            .no_sandbox()
            .args(vec![
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-extensions",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ])
            .build()
            .context("Failed to build browser config")?;

        let (browser, mut handler) = Browser::launch(config)
            .await
            .context("Failed to launch browser")?;

        // Spawn a task to handle browser events
        tokio::spawn(async move {
            while let Some(h) = handler.next().await {
                if h.is_err() {
                    warn!("Browser handler error: {:?}", h);
                }
            }
        });

        info!("Headless Chrome browser initialized successfully");
        Ok(Self { browser: Arc::new(browser) })
    }

    pub async fn capture_screenshot(
        &self,
        url: &str,
        viewport: &Viewport,
        wait_ms: Option<u64>,
    ) -> Result<Vec<u8>> {
        debug!("Capturing screenshot for {} at {}x{}", url, viewport.width, viewport.height);

        // Create a new page
        let page = self.browser
            .new_page("about:blank")
            .await
            .context("Failed to create new page")?;

        // Set viewport
        page.execute(
            chromiumoxide::cdp::browser_protocol::emulation::SetDeviceMetricsOverrideParams::builder()
                .width(viewport.width as i64)
                .height(viewport.height as i64)
                .device_scale_factor(1.0)
                .mobile(viewport.width < 768)
                .build()
        )
        .await
        .context("Failed to set viewport")?;

        // Navigate to URL
        page.goto(url)
            .await
            .context("Failed to navigate to URL")?;

        // Wait for page to load
        page.wait_for_navigation()
            .await
            .context("Failed to wait for page load")?;

        // Additional wait if specified
        if let Some(wait_time) = wait_ms {
            debug!("Waiting additional {}ms for page to settle", wait_time);
            sleep(Duration::from_millis(wait_time)).await;
        }

        // Wait for network to be idle (no requests for 500ms)
        if let Err(e) = self.wait_for_network_idle(&page).await {
            warn!("Network idle wait failed: {}, continuing anyway", e);
        }

        // Capture screenshot
        let screenshot_data = page
            .screenshot(chromiumoxide::page::ScreenshotParams::builder()
                .format(chromiumoxide::cdp::browser_protocol::page::CaptureScreenshotFormat::Png)
                .full_page(true)
                .build())
            .await
            .context("Failed to capture screenshot")?;

        // Close the page
        if let Err(e) = page.close().await {
            warn!("Failed to close page: {}", e);
        }

        debug!("Screenshot captured successfully ({} bytes)", screenshot_data.len());
        Ok(screenshot_data)
    }

    async fn wait_for_network_idle(&self, page: &Page) -> Result<()> {
        let mut idle_count = 0;
        let required_idle_count = 5; // 500ms of idle (5 * 100ms checks)

        for _ in 0..50 { // Max 5 seconds wait
            sleep(Duration::from_millis(100)).await;
            
            // Check if there are any pending network requests
            // This is a simplified check - in production you might want more sophisticated logic
            let performance_metrics = page
                .evaluate("performance.getEntriesByType('navigation').length")
                .await;

            match performance_metrics {
                Ok(_) => {
                    idle_count += 1;
                    if idle_count >= required_idle_count {
                        debug!("Network appears to be idle");
                        return Ok(());
                    }
                }
                Err(_) => {
                    idle_count = 0; // Reset counter on any activity
                }
            }
        }

        debug!("Network idle wait timeout, proceeding anyway");
        Ok(())
    }

    pub async fn get_page_info(&self, url: &str) -> Result<PageInfo> {
        let page = self.browser
            .new_page("about:blank")
            .await
            .context("Failed to create new page")?;

        page.goto(url)
            .await
            .context("Failed to navigate to URL")?;

        page.wait_for_navigation()
            .await
            .context("Failed to wait for page load")?;

        // Get page title
        let title = page
            .evaluate("document.title")
            .await
            .and_then(|result| Ok(result.into_value::<String>()?))
            .unwrap_or_else(|_| "Unknown".to_string());

        // Get viewport size
        let viewport_result = page
            .evaluate("({ width: window.innerWidth, height: window.innerHeight })")
            .await
            .context("Failed to get viewport size")?;

        let viewport_value = viewport_result.into_value::<serde_json::Value>()
            .context("Failed to parse viewport size")?;

        let actual_width = viewport_value["width"].as_u64().unwrap_or(1920) as u32;
        let actual_height = viewport_value["height"].as_u64().unwrap_or(1080) as u32;

        // Close the page
        if let Err(e) = page.close().await {
            warn!("Failed to close page: {}", e);
        }

        Ok(PageInfo {
            title,
            actual_viewport: Viewport {
                width: actual_width,
                height: actual_height,
                device_name: "detected".to_string(),
            },
        })
    }
}

#[derive(Debug)]
pub struct PageInfo {
    pub title: String,
    pub actual_viewport: Viewport,
}