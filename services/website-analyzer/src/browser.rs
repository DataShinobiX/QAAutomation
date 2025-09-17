use anyhow::{Context, Result};
use fantoccini::{ClientBuilder, Locator};
use shared::{
    DomElement, FormElement, ImageElement, InputElement, LinkElement, PerformanceMetrics,
    WebsiteAnalysis,
};
use std::{collections::HashMap, time::Instant};
use tokio::time::{sleep, Duration};
use tracing::{debug, warn, info};
use serde_json::json;
use chrono::Utc;
use uuid::Uuid;

#[derive(Clone)]
pub struct BrowserAnalyzer {
    webdriver_url: String,
}

impl BrowserAnalyzer {
    pub async fn new() -> Result<Self> {
        info!("Initializing Browser Analyzer with WebDriver...");
        
        let webdriver_url = std::env::var("WEBDRIVER_URL")
            .unwrap_or_else(|_| "http://localhost:4444".to_string());
        
        // Test WebDriver connection
        match Self::test_webdriver_connection(&webdriver_url).await {
            Ok(_) => {
                info!("WebDriver connection successful at {}", webdriver_url);
            }
            Err(e) => {
                warn!("WebDriver not available at {}: {}", webdriver_url, e);
                info!("Falling back to scraper mode. To use real browser:");
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

    pub async fn analyze(&self, url: &str) -> Result<WebsiteAnalysis> {
        debug!("Starting browser analysis for: {}", url);
        let start_time = Instant::now();

        // Try to use real WebDriver first
        match self.analyze_with_browser(url, start_time).await {
            Ok(analysis) => {
                info!("Browser analysis completed successfully for {}", url);
                Ok(analysis)
            }
            Err(e) => {
                warn!("Browser analysis failed: {}, falling back to scraper", e);
                // Fallback to scraper-based analysis
                self.analyze_with_scraper(url, start_time).await
            }
        }
    }

    async fn analyze_with_browser(&self, url: &str, start_time: Instant) -> Result<WebsiteAnalysis> {
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
                "--window-size=1920,1080",
                "--ignore-certificate-errors",
                "--allow-running-insecure-content",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=VizDisplayCompositor",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
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
            .set_window_size(1920, 1080)
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

        // Extended wait for React SPAs
        sleep(Duration::from_millis(3000)).await;
        
        // Check if this is a React app and wait for it to load
        let is_react_app = self.check_if_react_app(&client).await.unwrap_or(false);
        if is_react_app {
            info!("Detected React SPA, waiting for app to fully load...");
            
            // Check for JavaScript errors first
            self.check_js_errors(&client).await;
            
            // Wait for React root to have content with more attempts
            for attempt in 1..=15 {
                let has_content = self.check_react_content_loaded(&client).await.unwrap_or(false);
                if has_content {
                    info!("React app loaded successfully after {} attempts", attempt);
                    break;
                }
                
                // Log current state for debugging
                if attempt % 3 == 0 {
                    let current_content = self.get_current_dom_state(&client).await.unwrap_or_default();
                    info!("Attempt {}/15 - Current DOM state: {}", attempt, current_content);
                }
                
                info!("Waiting for React app to load... attempt {}/15", attempt);
                sleep(Duration::from_millis(3000)).await; // Increased wait time
            }
            
            // Final wait for any remaining network requests
            sleep(Duration::from_millis(3000)).await;
        } else {
            // Standard wait for non-SPA sites
            sleep(Duration::from_millis(2000)).await;
        }

        let load_time = start_time.elapsed();

        // Extract page information using browser
        let page_title = self.extract_page_title_browser(&client).await?;
        let meta_description = self.extract_meta_description_browser(&client).await?;
        let dom_structure = self.extract_dom_structure_browser(&client).await?;
        let form_elements = self.extract_forms_browser(&client).await?;
        let links = self.extract_links_browser(&client, url).await?;
        let images = self.extract_images_browser(&client, url).await?;
        let performance_metrics = self.get_performance_metrics_browser(&client, load_time).await?;

        // Close the browser session
        if let Err(e) = client.close().await {
            warn!("Failed to close browser session: {}", e);
        }

        let analysis = WebsiteAnalysis {
            url: url.to_string(),
            timestamp: Utc::now(),
            analysis_id: Uuid::new_v4(),
            page_title,
            meta_description,
            dom_structure,
            form_elements,
            links,
            images,
            performance_metrics: Some(performance_metrics),
        };

        debug!("Browser analysis completed for: {}", url);
        Ok(analysis)
    }

    async fn extract_page_title_browser(&self, client: &fantoccini::Client) -> Result<Option<String>> {
        match client.title().await {
            Ok(title) if !title.trim().is_empty() => Ok(Some(title.trim().to_string())),
            _ => Ok(None)
        }
    }

    async fn extract_meta_description_browser(&self, client: &fantoccini::Client) -> Result<Option<String>> {
        let script = r#"
            const meta = document.querySelector('meta[name="description"]');
            return meta ? meta.getAttribute('content') : null;
        "#;
        
        match client.execute(script, vec![]).await {
            Ok(result) => {
                if let Some(description) = result.as_str() {
                    if !description.trim().is_empty() {
                        return Ok(Some(description.trim().to_string()));
                    }
                }
                Ok(None)
            }
            Err(_) => Ok(None)
        }
    }

    async fn extract_dom_structure_browser(&self, client: &fantoccini::Client) -> Result<DomElement> {
        let script = r#"
            function elementToObject(element, xpath, cssSelector, depth = 0) {
                if (depth > 8) return null; // Limit depth to prevent huge structures
                
                const obj = {
                    tag: element.tagName.toLowerCase(),
                    id: element.id || null,
                    classes: element.className ? element.className.split(' ').filter(c => c) : [],
                    attributes: {},
                    text_content: null,
                    children: [],
                    xpath: xpath,
                    css_selector: cssSelector
                };
                
                // Get attributes
                for (let attr of element.attributes) {
                    obj.attributes[attr.name] = attr.value;
                }
                
                // Get direct text content (not from children)
                const textNodes = Array.from(element.childNodes)
                    .filter(node => node.nodeType === Node.TEXT_NODE)
                    .map(node => node.textContent.trim())
                    .filter(text => text.length > 0);
                
                if (textNodes.length > 0) {
                    obj.text_content = textNodes.join(' ');
                }
                
                // Get children elements
                const children = Array.from(element.children);
                obj.children = children.map((child, index) => {
                    const childXpath = `${xpath}/*[${index + 1}]`;
                    const childCss = `${cssSelector} > *:nth-child(${index + 1})`;
                    return elementToObject(child, childXpath, childCss, depth + 1);
                }).filter(child => child !== null);
                
                return obj;
            }
            
            const body = document.body || document.documentElement;
            return elementToObject(body, '/html/body', 'body');
        "#;

        let result = client.execute(script, vec![]).await
            .context("Failed to extract DOM structure")?;
        
        let dom_data: DomElement = serde_json::from_value(result)
            .context("Failed to parse DOM structure from browser")?;
        
        Ok(dom_data)
    }

    async fn extract_forms_browser(&self, client: &fantoccini::Client) -> Result<Vec<FormElement>> {
        let script = r#"
            const forms = Array.from(document.querySelectorAll('form'));
            return forms.map((form, formIndex) => {
                const inputs = Array.from(form.querySelectorAll('input, textarea, select'));
                return {
                    id: form.id || null,
                    action: form.action || null,
                    method: form.method || 'get',
                    inputs: inputs.map((input, inputIndex) => ({
                        input_type: input.type || 'text',
                        name: input.name || null,
                        id: input.id || null,
                        placeholder: input.placeholder || null,
                        required: input.required || false,
                        xpath: `//form[${formIndex + 1}]//input[${inputIndex + 1}]`
                    })),
                    xpath: `//form[${formIndex + 1}]`
                };
            });
        "#;

        let result = client.execute(script, vec![]).await
            .context("Failed to extract forms")?;
        
        let forms: Vec<FormElement> = serde_json::from_value(result)
            .context("Failed to parse forms from browser")?;
        
        Ok(forms)
    }

    async fn extract_links_browser(&self, client: &fantoccini::Client, _base_url: &str) -> Result<Vec<LinkElement>> {
        let script = r#"
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links.map((link, index) => {
                const url = new URL(link.href, window.location.href);
                return {
                    href: url.href,
                    text: link.textContent.trim(),
                    title: link.title || null,
                    target: link.target || null,
                    xpath: `//a[${index + 1}]`
                };
            });
        "#;

        let result = client.execute(script, vec![]).await
            .context("Failed to extract links")?;
        
        let links: Vec<LinkElement> = serde_json::from_value(result)
            .context("Failed to parse links from browser")?;
        
        Ok(links)
    }

    async fn extract_images_browser(&self, client: &fantoccini::Client, _base_url: &str) -> Result<Vec<ImageElement>> {
        let script = r#"
            const images = Array.from(document.querySelectorAll('img[src]'));
            return images.map((img, index) => {
                const url = new URL(img.src, window.location.href);
                return {
                    src: url.href,
                    alt: img.alt || null,
                    width: img.width || null,
                    height: img.height || null,
                    xpath: `//img[${index + 1}]`
                };
            });
        "#;

        let result = client.execute(script, vec![]).await
            .context("Failed to extract images")?;
        
        let images: Vec<ImageElement> = serde_json::from_value(result)
            .context("Failed to parse images from browser")?;
        
        Ok(images)
    }

    async fn get_performance_metrics_browser(&self, client: &fantoccini::Client, load_time: std::time::Duration) -> Result<PerformanceMetrics> {
        let script = r#"
            const navigation = performance.getEntriesByType('navigation')[0];
            const paint = performance.getEntriesByType('paint');
            
            let firstPaint = null;
            let largestContentfulPaint = null;
            
            const firstPaintEntry = paint.find(entry => entry.name === 'first-paint');
            if (firstPaintEntry) {
                firstPaint = Math.round(firstPaintEntry.startTime);
            }
            
            // Try to get LCP
            try {
                const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                if (lcpEntries.length > 0) {
                    largestContentfulPaint = Math.round(lcpEntries[lcpEntries.length - 1].startTime);
                }
            } catch (e) {
                // LCP not available
            }
            
            return {
                domContentLoaded: navigation ? Math.round(navigation.domContentLoadedEventEnd) : null,
                firstPaint: firstPaint,
                largestContentfulPaint: largestContentfulPaint
            };
        "#;

        match client.execute(script, vec![]).await {
            Ok(result) => {
                let perf_data: serde_json::Value = result;
                
                let dom_content_loaded_ms = perf_data["domContentLoaded"]
                    .as_u64()
                    .unwrap_or(load_time.as_millis() as u64);
                
                let first_paint_ms = perf_data["firstPaint"].as_u64();
                let largest_contentful_paint_ms = perf_data["largestContentfulPaint"].as_u64();
                
                Ok(PerformanceMetrics {
                    load_time_ms: load_time.as_millis() as u64,
                    dom_content_loaded_ms,
                    first_paint_ms,
                    largest_contentful_paint_ms,
                })
            }
            Err(_) => {
                Ok(PerformanceMetrics {
                    load_time_ms: load_time.as_millis() as u64,
                    dom_content_loaded_ms: load_time.as_millis() as u64,
                    first_paint_ms: None,
                    largest_contentful_paint_ms: None,
                })
            }
        }
    }

    // Fallback to the original scraper-based analysis
    async fn analyze_with_scraper(&self, url: &str, start_time: Instant) -> Result<WebsiteAnalysis> {
        debug!("Falling back to scraper analysis for: {}", url);
        
        // Use the original scraper logic as fallback
        let client = reqwest::Client::builder()
            .user_agent("QA-Automation-Bot/1.0")
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .context("Failed to create HTTP client")?;

        // Fetch the webpage
        let response = client
            .get(url)
            .send()
            .await
            .context("Failed to fetch webpage")?;

        let status = response.status();
        if !status.is_success() {
            return Err(anyhow::anyhow!("HTTP request failed with status: {}", status));
        }

        let html_content = response.text().await.context("Failed to read response body")?;
        let load_time = start_time.elapsed();

        // Parse HTML using scraper as fallback
        use scraper::Html;
        let document = Html::parse_document(&html_content);

        // Use scraper-based extraction methods (simplified versions)
        let page_title = self.extract_page_title_scraper(&document);
        let meta_description = self.extract_meta_description_scraper(&document);
        let dom_structure = self.extract_dom_structure_scraper(&document)?;
        let form_elements = self.extract_forms_scraper(&document);
        let links = self.extract_links_scraper(&document, url)?;
        let images = self.extract_images_scraper(&document, url)?;

        let performance_metrics = PerformanceMetrics {
            load_time_ms: load_time.as_millis() as u64,
            dom_content_loaded_ms: load_time.as_millis() as u64,
            first_paint_ms: None,
            largest_contentful_paint_ms: None,
        };

        let analysis = WebsiteAnalysis {
            url: url.to_string(),
            timestamp: Utc::now(),
            analysis_id: Uuid::new_v4(),
            page_title,
            meta_description,
            dom_structure,
            form_elements,
            links,
            images,
            performance_metrics: Some(performance_metrics),
        };

        debug!("Scraper fallback analysis completed for: {}", url);
        Ok(analysis)
    }

    // Scraper-based fallback methods (simplified versions of the original analyzer.rs methods)
    fn extract_page_title_scraper(&self, document: &scraper::Html) -> Option<String> {
        use scraper::Selector;
        let title_selector = Selector::parse("title").ok()?;
        document
            .select(&title_selector)
            .next()
            .map(|element| element.text().collect::<String>().trim().to_string())
            .filter(|title| !title.is_empty())
    }

    fn extract_meta_description_scraper(&self, document: &scraper::Html) -> Option<String> {
        use scraper::Selector;
        let meta_selector = Selector::parse("meta[name='description']").ok()?;
        document
            .select(&meta_selector)
            .next()
            .and_then(|element| element.value().attr("content"))
            .map(|content| content.trim().to_string())
            .filter(|desc| !desc.is_empty())
    }

    fn extract_dom_structure_scraper(&self, document: &scraper::Html) -> Result<DomElement> {
        use scraper::Selector;
        let body_selector = Selector::parse("body").map_err(|e| anyhow::anyhow!("Failed to create body selector: {:?}", e))?;
        
        if let Some(body_element) = document.select(&body_selector).next() {
            Ok(self.element_to_dom_element_scraper(body_element, "/html/body", "body"))
        } else {
            let html_selector = Selector::parse("html").map_err(|e| anyhow::anyhow!("Failed to create html selector: {:?}", e))?;
            if let Some(html_element) = document.select(&html_selector).next() {
                Ok(self.element_to_dom_element_scraper(html_element, "/html", "html"))
            } else {
                Err(anyhow::anyhow!("No HTML structure found"))
            }
        }
    }

    fn element_to_dom_element_scraper(&self, element: scraper::ElementRef, xpath: &str, css_selector: &str) -> DomElement {
        let tag = element.value().name().to_string();
        let id = element.value().attr("id").map(|s| s.to_string());
        let classes = element
            .value()
            .attr("class")
            .map(|class_str| {
                class_str
                    .split_whitespace()
                    .map(|s| s.to_string())
                    .collect()
            })
            .unwrap_or_default();

        let mut attributes = HashMap::new();
        for attr in element.value().attrs() {
            attributes.insert(attr.0.to_string(), attr.1.to_string());
        }

        let text_content = element
            .text()
            .collect::<String>()
            .trim()
            .to_string();
        let text_content = if text_content.is_empty() {
            None
        } else {
            Some(text_content)
        };

        // Limit depth for scraper fallback
        let children = if xpath.matches('/').count() < 8 {
            element
                .children()
                .filter_map(|child_node| scraper::ElementRef::wrap(child_node))
                .enumerate()
                .map(|(index, child_element)| {
                    let child_xpath = format!("{}/*[{}]", xpath, index + 1);
                    let child_css = format!("{} > *:nth-child({})", css_selector, index + 1);
                    self.element_to_dom_element_scraper(child_element, &child_xpath, &child_css)
                })
                .collect()
        } else {
            Vec::new()
        };

        DomElement {
            tag,
            id,
            classes,
            attributes,
            text_content,
            children,
            xpath: xpath.to_string(),
            css_selector: css_selector.to_string(),
        }
    }

    fn extract_forms_scraper(&self, document: &scraper::Html) -> Vec<FormElement> {
        use scraper::Selector;
        let form_selector = match Selector::parse("form") {
            Ok(selector) => selector,
            Err(_) => return Vec::new(),
        };

        document
            .select(&form_selector)
            .enumerate()
            .map(|(index, form_element)| {
                let id = form_element.value().attr("id").map(|s| s.to_string());
                let action = form_element.value().attr("action").map(|s| s.to_string());
                let method = form_element
                    .value()
                    .attr("method")
                    .unwrap_or("get")
                    .to_string();

                let input_selector = Selector::parse("input, textarea, select").unwrap();
                let inputs = form_element
                    .select(&input_selector)
                    .enumerate()
                    .map(|(input_index, input_element)| {
                        let input_type = input_element
                            .value()
                            .attr("type")
                            .unwrap_or("text")
                            .to_string();
                        let name = input_element.value().attr("name").map(|s| s.to_string());
                        let id = input_element.value().attr("id").map(|s| s.to_string());
                        let placeholder = input_element
                            .value()
                            .attr("placeholder")
                            .map(|s| s.to_string());
                        let required = input_element.value().attr("required").is_some();

                        InputElement {
                            input_type,
                            name,
                            id,
                            placeholder,
                            required,
                            xpath: format!("//form[{}]//input[{}]", index + 1, input_index + 1),
                        }
                    })
                    .collect();

                FormElement {
                    id,
                    action,
                    method,
                    inputs,
                    xpath: format!("//form[{}]", index + 1),
                }
            })
            .collect()
    }

    fn extract_links_scraper(&self, document: &scraper::Html, base_url: &str) -> Result<Vec<LinkElement>> {
        use scraper::Selector;
        let link_selector = Selector::parse("a[href]").map_err(|e| anyhow::anyhow!("Failed to create link selector: {:?}", e))?;
        let base_url = url::Url::parse(base_url).context("Invalid base URL")?;

        Ok(document
            .select(&link_selector)
            .enumerate()
            .filter_map(|(index, link_element)| {
                let href = link_element.value().attr("href")?;
                
                let absolute_href = match base_url.join(href) {
                    Ok(url) => url.to_string(),
                    Err(_) => {
                        warn!("Failed to resolve URL: {}", href);
                        href.to_string()
                    }
                };

                let text = link_element.text().collect::<String>().trim().to_string();
                let title = link_element.value().attr("title").map(|s| s.to_string());
                let target = link_element.value().attr("target").map(|s| s.to_string());

                Some(LinkElement {
                    href: absolute_href,
                    text,
                    title,
                    target,
                    xpath: format!("//a[{}]", index + 1),
                })
            })
            .collect())
    }

    fn extract_images_scraper(&self, document: &scraper::Html, base_url: &str) -> Result<Vec<ImageElement>> {
        use scraper::Selector;
        let img_selector = Selector::parse("img[src]").map_err(|e| anyhow::anyhow!("Failed to create img selector: {:?}", e))?;
        let base_url = url::Url::parse(base_url).context("Invalid base URL")?;

        Ok(document
            .select(&img_selector)
            .enumerate()
            .filter_map(|(index, img_element)| {
                let src = img_element.value().attr("src")?;
                
                let absolute_src = match base_url.join(src) {
                    Ok(url) => url.to_string(),
                    Err(_) => {
                        warn!("Failed to resolve image URL: {}", src);
                        src.to_string()
                    }
                };

                let alt = img_element.value().attr("alt").map(|s| s.to_string());
                let width = img_element
                    .value()
                    .attr("width")
                    .and_then(|w| w.parse().ok());
                let height = img_element
                    .value()
                    .attr("height")
                    .and_then(|h| h.parse().ok());

                Some(ImageElement {
                    src: absolute_src,
                    alt,
                    width,
                    height,
                    xpath: format!("//img[{}]", index + 1),
                })
            })
            .collect())
    }

    async fn check_if_react_app(&self, client: &fantoccini::Client) -> Result<bool> {
        let script = r#"
            return !!(window.React || 
                     window.__REACT_DEVTOOLS_GLOBAL_HOOK__ ||
                     document.querySelector('[data-reactroot]') ||
                     document.querySelector('#root') ||
                     document.querySelector('#app') ||
                     document.body.innerHTML.includes('react'));
        "#;
        
        match client.execute(script, vec![]).await {
            Ok(result) => Ok(result.as_bool().unwrap_or(false)),
            Err(_) => Ok(false)
        }
    }

    async fn check_react_content_loaded(&self, client: &fantoccini::Client) -> Result<bool> {
        let script = r#"
            const root = document.querySelector('#root');
            if (!root) return false;
            
            // Check if root has meaningful content (not just the noscript message)
            const hasContent = root.children.length > 0 && 
                              root.textContent.trim().length > 100 &&
                              !root.textContent.includes('You need to enable JavaScript');
            
            // Also check for common React indicators
            const hasReactElements = document.querySelector('[data-testid]') ||
                                   document.querySelector('.react-') ||
                                   document.querySelectorAll('div').length > 5 ||
                                   document.querySelector('input') ||
                                   document.querySelector('form') ||
                                   document.querySelector('button');
            
            return hasContent || hasReactElements;
        "#;
        
        match client.execute(script, vec![]).await {
            Ok(result) => Ok(result.as_bool().unwrap_or(false)),
            Err(_) => Ok(false)
        }
    }

    async fn check_js_errors(&self, client: &fantoccini::Client) {
        let script = r#"
            const errors = [];
            const originalError = window.console.error;
            window.console.error = function(...args) {
                errors.push(args.join(' '));
                originalError.apply(console, args);
            };
            return errors;
        "#;
        
        if let Ok(result) = client.execute(script, vec![]).await {
            if let Some(errors) = result.as_array() {
                if !errors.is_empty() {
                    info!("JavaScript errors detected: {:?}", errors);
                }
            }
        }
    }

    async fn get_current_dom_state(&self, client: &fantoccini::Client) -> Result<String> {
        let script = r#"
            const root = document.querySelector('#root');
            return {
                hasRoot: !!root,
                rootChildren: root ? root.children.length : 0,
                rootContent: root ? root.textContent.slice(0, 100) : 'no root',
                totalElements: document.querySelectorAll('*').length,
                hasInputs: !!document.querySelector('input'),
                hasForms: !!document.querySelector('form'),
                hasButtons: !!document.querySelector('button')
            };
        "#;
        
        match client.execute(script, vec![]).await {
            Ok(result) => Ok(format!("{:?}", result)),
            Err(_) => Ok("Unable to get DOM state".to_string())
        }
    }
}