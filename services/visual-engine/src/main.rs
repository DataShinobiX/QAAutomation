use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tracing::{info, error};
use uuid::Uuid;

pub mod browser_real;
pub mod comparison;
pub mod storage;
pub mod models;

use browser_real::BrowserEngine;
use comparison::ImageComparator;
use storage::StorageManager;
use shared::{VisualTest, Screenshot, Viewport};

#[derive(Clone)]
pub struct AppState {
    browser: BrowserEngine,
    comparator: ImageComparator,
    storage: StorageManager,
}

#[derive(Debug, Deserialize)]
pub struct CaptureRequest {
    pub url: String,
    pub viewports: Option<Vec<ViewportRequest>>,
    pub wait_ms: Option<u64>,
}

#[derive(Debug, Deserialize)]
pub struct ViewportRequest {
    pub width: u32,
    pub height: u32,
    pub device_name: String,
}

#[derive(Debug, Deserialize)]
pub struct CompareRequest {
    pub baseline_screenshot_id: Uuid,
    pub current_screenshot_id: Uuid,
    pub threshold: Option<f64>,
}

#[derive(Debug, Serialize)]
pub struct CaptureResponse {
    pub visual_test_id: Uuid,
    pub screenshots: Vec<Screenshot>,
}

#[derive(Debug, Serialize)]
pub struct CompareResponse {
    pub comparison_id: Uuid,
    pub passed: bool,
    pub difference_percentage: f64,
    pub different_pixels: u64,
    pub total_pixels: u64,
    pub diff_image_url: Option<String>,
}

impl Default for ViewportRequest {
    fn default() -> Self {
        Self {
            width: 1920,
            height: 1080,
            device_name: "desktop".to_string(),
        }
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Load environment variables
    dotenvy::dotenv().ok();

    info!("Initializing Visual Engine services...");

    // Initialize components
    let browser = BrowserEngine::new().await?;
    let comparator = ImageComparator::new();
    let storage = match StorageManager::new().await {
        Ok(storage) => {
            info!("Storage manager initialized successfully");
            storage
        }
        Err(e) => {
            error!("Failed to initialize storage manager: {}", e);
            info!("This usually means MinIO is not accessible. Please ensure MinIO is running with:");
            info!("  docker compose up -d minio");
            return Err(e);
        }
    };

    info!("Visual Engine services initialized successfully");

    // Create application state
    let state = AppState {
        browser,
        comparator,
        storage,
    };

    // Build our application with routes
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/capture", post(capture_screenshots))
        .route("/compare", post(compare_screenshots))
        .route("/screenshots/:id", get(get_screenshot))
        .route("/visual-tests", get(get_visual_tests))
        .route("/visual-tests/:id", get(get_visual_test))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3002").await?;
    info!("Visual Engine service starting on port 3002");

    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check() -> &'static str {
    "Visual Engine Service is healthy"
}

async fn capture_screenshots(
    State(state): State<AppState>,
    Json(request): Json<CaptureRequest>,
) -> Result<Json<CaptureResponse>, StatusCode> {
    info!("Capturing screenshots for URL: {}", request.url);

    // Use default viewports if none provided
    let viewports = request.viewports.unwrap_or_else(|| vec![
        ViewportRequest { width: 1920, height: 1080, device_name: "desktop".to_string() },
        ViewportRequest { width: 768, height: 1024, device_name: "tablet".to_string() },
        ViewportRequest { width: 375, height: 667, device_name: "mobile".to_string() },
    ]);

    let mut screenshots = Vec::new();
    let visual_test_id = Uuid::new_v4();

    for viewport_req in viewports {
        let viewport = Viewport {
            width: viewport_req.width,
            height: viewport_req.height,
            device_name: viewport_req.device_name,
        };

        match state.browser.capture_screenshot(&request.url, &viewport, request.wait_ms).await {
            Ok(screenshot_data) => {
                match state.storage.store_screenshot(screenshot_data, &viewport, &request.url).await {
                    Ok(screenshot) => {
                        screenshots.push(screenshot);
                        info!("Screenshot captured for viewport: {}x{}", viewport.width, viewport.height);
                    }
                    Err(e) => {
                        error!("Failed to store screenshot: {}", e);
                        return Err(StatusCode::INTERNAL_SERVER_ERROR);
                    }
                }
            }
            Err(e) => {
                error!("Failed to capture screenshot: {}", e);
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }
        }
    }

    info!("Captured {} screenshots for {}", screenshots.len(), request.url);

    Ok(Json(CaptureResponse {
        visual_test_id,
        screenshots,
    }))
}

async fn compare_screenshots(
    State(state): State<AppState>,
    Json(request): Json<CompareRequest>,
) -> Result<Json<CompareResponse>, StatusCode> {
    info!("Comparing screenshots: {} vs {}", request.baseline_screenshot_id, request.current_screenshot_id);

    let threshold = request.threshold.unwrap_or(0.1); // Default 0.1% difference threshold

    match state.comparator.compare_screenshots(
        request.baseline_screenshot_id,
        request.current_screenshot_id,
        threshold,
        &state.storage,
    ).await {
        Ok(comparison) => {
            info!("Screenshot comparison completed: {}% difference", comparison.difference_percentage);
            
            Ok(Json(CompareResponse {
                comparison_id: comparison.id,
                passed: comparison.passed,
                difference_percentage: comparison.difference_percentage,
                different_pixels: comparison.different_pixels,
                total_pixels: comparison.total_pixels,
                diff_image_url: comparison.diff_image_path,
            }))
        }
        Err(e) => {
            error!("Screenshot comparison failed: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_screenshot(
    State(state): State<AppState>,
    axum::extract::Path(id): axum::extract::Path<Uuid>,
) -> Result<Json<Screenshot>, StatusCode> {
    match state.storage.get_screenshot(id).await {
        Ok(Some(screenshot)) => Ok(Json(screenshot)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            error!("Failed to get screenshot: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_visual_tests(
    State(state): State<AppState>,
) -> Result<Json<Vec<VisualTest>>, StatusCode> {
    match state.storage.get_visual_tests(10).await {
        Ok(tests) => Ok(Json(tests)),
        Err(e) => {
            error!("Failed to get visual tests: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_visual_test(
    State(state): State<AppState>,
    axum::extract::Path(id): axum::extract::Path<Uuid>,
) -> Result<Json<VisualTest>, StatusCode> {
    match state.storage.get_visual_test(id).await {
        Ok(Some(test)) => Ok(Json(test)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            error!("Failed to get visual test: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}