use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DomElement {
    pub tag: String,
    pub id: Option<String>,
    pub classes: Vec<String>,
    pub attributes: std::collections::HashMap<String, String>,
    pub text_content: Option<String>,
    pub children: Vec<DomElement>,
    pub xpath: String,
    pub css_selector: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebsiteAnalysis {
    pub url: String,
    pub timestamp: DateTime<Utc>,
    pub analysis_id: Uuid,
    pub page_title: Option<String>,
    pub meta_description: Option<String>,
    pub dom_structure: DomElement,
    pub form_elements: Vec<FormElement>,
    pub links: Vec<LinkElement>,
    pub images: Vec<ImageElement>,
    pub performance_metrics: Option<PerformanceMetrics>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FormElement {
    pub id: Option<String>,
    pub action: Option<String>,
    pub method: String,
    pub inputs: Vec<InputElement>,
    pub xpath: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InputElement {
    pub input_type: String,
    pub name: Option<String>,
    pub id: Option<String>,
    pub placeholder: Option<String>,
    pub required: bool,
    pub xpath: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LinkElement {
    pub href: String,
    pub text: String,
    pub title: Option<String>,
    pub target: Option<String>,
    pub xpath: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ImageElement {
    pub src: String,
    pub alt: Option<String>,
    pub width: Option<u32>,
    pub height: Option<u32>,
    pub xpath: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub load_time_ms: u64,
    pub dom_content_loaded_ms: u64,
    pub first_paint_ms: Option<u64>,
    pub largest_contentful_paint_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestCase {
    pub id: Uuid,
    pub name: String,
    pub description: String,
    pub test_type: TestType,
    pub target_element: Option<String>, // CSS selector or XPath
    pub expected_value: Option<String>,
    pub actions: Vec<TestAction>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TestType {
    ElementExists,
    ElementVisible,
    ElementText,
    ElementAttribute,
    PageTitle,
    FormSubmission,
    Navigation,
    VisualRegression,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TestAction {
    pub action_type: ActionType,
    pub target: String, // CSS selector or XPath
    pub value: Option<String>,
    pub wait_after_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ActionType {
    Click,
    Type,
    Wait,
    Navigate,
    Screenshot,
    Scroll,
}

// Visual Engine Types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VisualTest {
    pub id: Uuid,
    pub url: String,
    pub timestamp: DateTime<Utc>,
    pub screenshots: Vec<Screenshot>,
    pub comparison_result: Option<VisualComparison>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Screenshot {
    pub id: Uuid,
    pub viewport: Viewport,
    pub file_path: String, // Path in MinIO/S3
    pub file_size: u64,
    pub width: u32,
    pub height: u32,
    pub format: ImageFormat,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Viewport {
    pub width: u32,
    pub height: u32,
    pub device_name: String, // "desktop", "tablet", "mobile"
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ImageFormat {
    PNG,
    JPEG,
    WEBP,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VisualComparison {
    pub id: Uuid,
    pub baseline_screenshot_id: Uuid,
    pub current_screenshot_id: Uuid,
    pub difference_percentage: f64,
    pub different_pixels: u64,
    pub total_pixels: u64,
    pub diff_image_path: Option<String>, // Path to difference image in storage
    pub passed: bool,
    pub threshold: f64,
    pub created_at: DateTime<Utc>,
}