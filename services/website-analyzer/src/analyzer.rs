use anyhow::{Context, Result};
use chrono::Utc;
use reqwest::Client;
use scraper::{Html, Selector};
use shared::{
    DomElement, FormElement, ImageElement, InputElement, LinkElement, PerformanceMetrics,
    WebsiteAnalysis,
};
use std::{collections::HashMap, time::Instant};
use tracing::{debug, warn};
use uuid::Uuid;

#[derive(Clone)]
pub struct WebsiteAnalyzer {
    client: Client,
}

impl WebsiteAnalyzer {
    pub fn new() -> Self {
        let client = Client::builder()
            .user_agent("QA-Automation-Bot/1.0")
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        Self { client }
    }

    pub async fn analyze(&self, url: &str) -> Result<WebsiteAnalysis> {
        debug!("Starting analysis for: {}", url);
        let start_time = Instant::now();

        // Fetch the webpage
        let response = self
            .client
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

        debug!("Fetched HTML content ({} bytes)", html_content.len());

        // Parse HTML
        let document = Html::parse_document(&html_content);

        // Extract various elements
        let page_title = self.extract_page_title(&document);
        let meta_description = self.extract_meta_description(&document);
        let dom_structure = self.extract_dom_structure(&document)?;
        let form_elements = self.extract_forms(&document);
        let links = self.extract_links(&document, url)?;
        let images = self.extract_images(&document, url)?;

        let performance_metrics = PerformanceMetrics {
            load_time_ms: load_time.as_millis() as u64,
            dom_content_loaded_ms: load_time.as_millis() as u64, // Simplified for now
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

        debug!("Analysis completed for: {}", url);
        Ok(analysis)
    }

    fn extract_page_title(&self, document: &Html) -> Option<String> {
        let title_selector = Selector::parse("title").ok()?;
        document
            .select(&title_selector)
            .next()
            .map(|element| element.text().collect::<String>().trim().to_string())
            .filter(|title| !title.is_empty())
    }

    fn extract_meta_description(&self, document: &Html) -> Option<String> {
        let meta_selector = Selector::parse("meta[name='description']").ok()?;
        document
            .select(&meta_selector)
            .next()
            .and_then(|element| element.value().attr("content"))
            .map(|content| content.trim().to_string())
            .filter(|desc| !desc.is_empty())
    }

    fn extract_dom_structure(&self, document: &Html) -> Result<DomElement> {
        let body_selector = Selector::parse("body").map_err(|e| anyhow::anyhow!("Failed to create body selector: {:?}", e))?;
        
        if let Some(body_element) = document.select(&body_selector).next() {
            Ok(self.element_to_dom_element(body_element, "/html/body", "body"))
        } else {
            // Fallback to html element if body not found
            let html_selector = Selector::parse("html").map_err(|e| anyhow::anyhow!("Failed to create html selector: {:?}", e))?;
            if let Some(html_element) = document.select(&html_selector).next() {
                Ok(self.element_to_dom_element(html_element, "/html", "html"))
            } else {
                Err(anyhow::anyhow!("No HTML structure found"))
            }
        }
    }

    fn element_to_dom_element(
        &self,
        element: scraper::ElementRef,
        xpath: &str,
        css_selector: &str,
    ) -> DomElement {
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

        // For now, we'll limit the depth to avoid infinite recursion and massive structures
        let children = if xpath.matches('/').count() < 10 {
            element
                .children()
                .filter_map(|child_node| {
                    if let Some(child_element) = scraper::ElementRef::wrap(child_node) {
                        Some(child_element)
                    } else {
                        None
                    }
                })
                .enumerate()
                .map(|(index, child_element)| {
                    let child_xpath = format!("{}/*[{}]", xpath, index + 1);
                    let child_css = format!("{} > *:nth-child({})", css_selector, index + 1);
                    self.element_to_dom_element(
                        child_element,
                        &child_xpath,
                        &child_css,
                    )
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

    fn extract_forms(&self, document: &Html) -> Vec<FormElement> {
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

    fn extract_links(&self, document: &Html, base_url: &str) -> Result<Vec<LinkElement>> {
        let link_selector = Selector::parse("a[href]").map_err(|e| anyhow::anyhow!("Failed to create link selector: {:?}", e))?;
        let base_url = url::Url::parse(base_url).context("Invalid base URL")?;

        Ok(document
            .select(&link_selector)
            .enumerate()
            .filter_map(|(index, link_element)| {
                let href = link_element.value().attr("href")?;
                
                // Resolve relative URLs
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

    fn extract_images(&self, document: &Html, base_url: &str) -> Result<Vec<ImageElement>> {
        let img_selector = Selector::parse("img[src]").map_err(|e| anyhow::anyhow!("Failed to create img selector: {:?}", e))?;
        let base_url = url::Url::parse(base_url).context("Invalid base URL")?;

        Ok(document
            .select(&img_selector)
            .enumerate()
            .filter_map(|(index, img_element)| {
                let src = img_element.value().attr("src")?;
                
                // Resolve relative URLs
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
}