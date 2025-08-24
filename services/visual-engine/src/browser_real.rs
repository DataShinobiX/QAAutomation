use anyhow::{Context, Result};
use fantoccini::{ClientBuilder, Locator};
use shared::Viewport;
use tokio::time::{sleep, Duration};
use tracing::{debug, warn, info};
use serde_json::json;
use base64::Engine;
use image::{RgbImage, Rgb};

#[derive(Clone)]
pub struct BrowserEngine {
    webdriver_url: String,
}

impl BrowserEngine {
    pub async fn new() -> Result<Self> {
        info!("Initializing Real Browser Engine with WebDriver...");
        
        let webdriver_url = std::env::var("WEBDRIVER_URL")
            .unwrap_or_else(|_| "http://localhost:4444".to_string());
        
        // Test WebDriver connection
        match Self::test_webdriver_connection(&webdriver_url).await {
            Ok(_) => {
                info!("WebDriver connection successful at {}", webdriver_url);
            }
            Err(e) => {
                warn!("WebDriver not available at {}: {}", webdriver_url, e);
                info!("Falling back to mock mode. To use real browser:");
                info!("1. Install Chrome/Chromium");
                info!("2. Download ChromeDriver from https://chromedriver.chromium.org/");
                info!("3. Run: chromedriver --port=4444");
                info!("4. Set WEBDRIVER_URL=http://localhost:4444");
            }
        }
        
        Ok(Self { webdriver_url })
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

    pub async fn capture_screenshot(
        &self,
        url: &str,
        viewport: &Viewport,
        wait_ms: Option<u64>,
    ) -> Result<Vec<u8>> {
        debug!("Capturing real screenshot for {} at {}x{}", url, viewport.width, viewport.height);

        // Try to use real WebDriver first
        match self.capture_real_screenshot(url, viewport, wait_ms).await {
            Ok(screenshot) => {
                info!("Real screenshot captured successfully ({} bytes)", screenshot.len());
                Ok(screenshot)
            }
            Err(e) => {
                warn!("Real screenshot failed: {}, falling back to mock", e);
                self.capture_mock_screenshot(viewport, wait_ms).await
            }
        }
    }

    async fn capture_real_screenshot(
        &self,
        url: &str,
        viewport: &Viewport,
        wait_ms: Option<u64>,
    ) -> Result<Vec<u8>> {
        // Create WebDriver capabilities for headless Chrome
        let mut caps = serde_json::Map::new();
        let chrome_opts = json!({
            "args": [
                "--headless",
                "--no-sandbox", 
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-web-security",
                format!("--window-size={},{}", viewport.width, viewport.height)
            ]
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
            .set_window_size(viewport.width, viewport.height)
            .await
            .context("Failed to set window size")?;

        // Navigate to URL
        client
            .goto(url)
            .await
            .context("Failed to navigate to URL")?;

        // Wait for page load
        client
            .wait()
            .for_element(Locator::Css("body"))
            .await
            .context("Failed to wait for page body")?;

        // Additional wait if specified
        if let Some(wait_time) = wait_ms {
            debug!("Waiting additional {}ms for page to settle", wait_time);
            sleep(Duration::from_millis(wait_time)).await;
        }

        // Wait for network idle (simplified)
        sleep(Duration::from_millis(1000)).await;

        // Capture screenshot
        let screenshot_base64 = client
            .screenshot()
            .await
            .context("Failed to capture screenshot")?;

        // Close the browser session
        if let Err(e) = client.close().await {
            warn!("Failed to close browser session: {}", e);
        }

        // Decode base64 screenshot
        let screenshot_data = base64::engine::general_purpose::STANDARD
            .decode(&screenshot_base64)
            .context("Failed to decode base64 screenshot")?;

        debug!("Real screenshot captured successfully ({} bytes)", screenshot_data.len());
        Ok(screenshot_data)
    }

    async fn capture_mock_screenshot(
        &self,
        viewport: &Viewport,
        wait_ms: Option<u64>,
    ) -> Result<Vec<u8>> {
        debug!("Capturing mock screenshot as fallback");
        
        // Simulate network delay
        if let Some(wait_time) = wait_ms {
            sleep(Duration::from_millis(wait_time)).await;
        } else {
            sleep(Duration::from_millis(500)).await;
        }

        // Create mock screenshot with "NO WEBDRIVER" overlay
        let mock_image = self.create_mock_screenshot_with_overlay(viewport)?;
        Ok(mock_image)
    }

    fn create_mock_screenshot_with_overlay(&self, viewport: &Viewport) -> Result<Vec<u8>> {
        use image::{ImageBuffer, Rgb, RgbImage};
        // Create a gradient background
        let mut img: RgbImage = ImageBuffer::from_fn(viewport.width, viewport.height, |x, y| {
            let r = ((x as f32 / viewport.width as f32) * 200.0) as u8 + 55;
            let g = ((y as f32 / viewport.height as f32) * 200.0) as u8 + 55;  
            let b = 100;
            Rgb([r, g, b])
        });

        // Note: Text overlay would require font files, so we create a simple gradient instead
        debug!("Creating mock screenshot {}x{} (WebDriver not available)", 
               viewport.width, viewport.height);
        
        // Add some visual elements to make it clear this is a mock
        self.add_mock_elements(&mut img, viewport);

        // Convert to PNG
        let mut png_data = Vec::new();
        let dynamic_img = image::DynamicImage::ImageRgb8(img);
        dynamic_img.write_to(&mut std::io::Cursor::new(&mut png_data), image::ImageFormat::Png)
            .context("Failed to encode mock image as PNG")?;

        Ok(png_data)
    }

    fn add_mock_elements(&self, img: &mut RgbImage, viewport: &Viewport) {
        // Add some geometric shapes to make it visually distinct
        use imageproc::drawing::{draw_filled_rect_mut, draw_hollow_rect_mut};
        use imageproc::rect::Rect;
        
        let white = Rgb([255, 255, 255]);
        let red = Rgb([255, 100, 100]);
        let blue = Rgb([100, 100, 255]);
        
        // Draw a header bar
        if viewport.height > 50 {
            draw_filled_rect_mut(img, Rect::at(0, 0).of_size(viewport.width, 50), red);
        }
        
        // Draw some content boxes
        let box_width = viewport.width / 4;
        let box_height = viewport.height / 6;
        
        for i in 0..3 {
            let x = (i * box_width + 20).min(viewport.width - box_width - 10) as i32;
            let y = (100 + i * (box_height + 20)).min(viewport.height - box_height - 10) as i32;
            
            if x > 0 && y > 0 {
                draw_hollow_rect_mut(img, Rect::at(x, y).of_size(box_width - 10, box_height), blue);
            }
        }
        
        // Add a footer
        if viewport.height > 100 {
            let footer_y = (viewport.height - 30) as i32;
            draw_filled_rect_mut(img, Rect::at(0, footer_y).of_size(viewport.width, 30), white);
        }
    }

    pub async fn get_page_info(&self, url: &str) -> Result<PageInfo> {
        debug!("Getting page info for: {}", url);
        
        // Try real browser first, fallback to mock
        match self.get_real_page_info(url).await {
            Ok(info) => Ok(info),
            Err(e) => {
                warn!("Failed to get real page info: {}, using mock", e);
                Ok(PageInfo {
                    title: format!("Mock Page Info for {}", url),
                    actual_viewport: Viewport {
                        width: 1920,
                        height: 1080,
                        device_name: "desktop-mock".to_string(),
                    },
                })
            }
        }
    }

    async fn get_real_page_info(&self, url: &str) -> Result<PageInfo> {
        let caps = serde_json::Map::new();
        let client = ClientBuilder::native()
            .capabilities(caps)
            .connect(&self.webdriver_url)
            .await
            .context("Failed to connect to WebDriver")?;

        client.goto(url).await.context("Failed to navigate to URL")?;

        // Get page title
        let title = client.title().await.unwrap_or_else(|_| "Unknown".to_string());

        // Get window size
        let (width, height) = client
            .get_window_size()
            .await
            .unwrap_or((1920, 1080));

        // Close session
        if let Err(e) = client.close().await {
            warn!("Failed to close browser session: {}", e);
        }

        Ok(PageInfo {
            title,
            actual_viewport: Viewport {
                width: width as u32,
                height: height as u32,
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