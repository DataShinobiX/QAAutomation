use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;
use tracing::{info, error, warn, Span};
use uuid::Uuid;

pub mod analyzer;
pub mod browser;
pub mod database;
pub mod models;

use browser::BrowserAnalyzer;
use database::DatabasePool;
use shared::WebsiteAnalysis;

#[derive(Clone)]
pub struct AppState {
    db_pool: DatabasePool,
    analyzer: BrowserAnalyzer,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct AnalyzeRequest {
    url: String,
}

#[derive(Debug, Serialize)]
pub struct AnalyzeResponse {
    analysis_id: Uuid,
    analysis: WebsiteAnalysis,
}

#[derive(Debug, Deserialize)]
pub struct GetAnalysisQuery {
    url: Option<String>,
    limit: Option<i64>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Load environment variables
    dotenvy::dotenv().ok();

    // Initialize database connection
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgresql://qa_user:qa_password@localhost:5433/qa_automation".to_string());
    
    let db_pool = DatabasePool::new(&database_url).await?;
    info!("Connected to database");

    // Initialize browser analyzer
    let analyzer = BrowserAnalyzer::new().await?;

    // Create application state
    let state = AppState {
        db_pool,
        analyzer,
    };

    // Build our application with routes
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/analyze", post(analyze_website))
        .route("/analyses", get(get_analyses))
        .route("/analyses/:id", get(get_analysis_by_id))
        .layer(
            TraceLayer::new_for_http()
                .make_span_with(|request: &axum::http::Request<_>| {
                    tracing::info_span!(
                        "http_request",
                        method = %request.method(),
                        uri = %request.uri(),
                        version = ?request.version(),
                    )
                })
                .on_request(|_request: &axum::http::Request<_>, _span: &Span| {
                    tracing::info!("→ Request received")
                })
                .on_response(|response: &axum::http::Response<_>, latency: std::time::Duration, _span: &Span| {
                    tracing::info!(
                        "← Response sent: {} in {:?}",
                        response.status(),
                        latency
                    )
                })
        )
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3001").await?;
    info!("Website Analyzer service starting on port 3001");

    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check() -> &'static str {
    info!("❤️  Health check requested - service is running");
    "Website Analyzer Service is healthy"
}

async fn analyze_website(
    State(state): State<AppState>,
    Json(request): Json<AnalyzeRequest>,
) -> Result<Json<AnalyzeResponse>, StatusCode> {
    let start_time = std::time::Instant::now();
    info!("🔍 Starting website analysis for: {}", request.url);
    info!("📋 Request payload: {}", serde_json::to_string(&request).unwrap_or_default());

    match state.analyzer.analyze(&request.url).await {
        Ok(analysis) => {
            let analysis_id = analysis.analysis_id;
            let analysis_duration = start_time.elapsed();
            
            info!("✅ Browser analysis successful for {} (took {:?})", request.url, analysis_duration);
            info!("📊 Analysis results: {} DOM elements, {} forms, {} links, {} images", 
                  count_dom_elements(&analysis.dom_structure),
                  analysis.form_elements.len(),
                  analysis.links.len(), 
                  analysis.images.len());
            
            // Store analysis in database
            let db_start = std::time::Instant::now();
            if let Err(e) = state.db_pool.store_analysis(&analysis).await {
                error!("💾 Failed to store analysis in database: {}", e);
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }
            let db_duration = db_start.elapsed();
            info!("💾 Analysis stored in database (took {:?})", db_duration);

            let total_duration = start_time.elapsed();
            info!("🏁 Analysis completed for {} with ID {} (total time: {:?})", request.url, analysis_id, total_duration);

            let response = AnalyzeResponse {
                analysis_id,
                analysis,
            };
            info!("📤 Sending response for {}", request.url);

            Ok(Json(response))
        }
        Err(e) => {
            let failed_duration = start_time.elapsed();
            error!("❌ Analysis failed for {} after {:?}: {}", request.url, failed_duration, e);
            Err(StatusCode::BAD_REQUEST)
        }
    }
}

fn count_dom_elements(element: &shared::DomElement) -> usize {
    1 + element.children.iter().map(count_dom_elements).sum::<usize>()
}

async fn get_analyses(
    State(state): State<AppState>,
    Query(query): Query<GetAnalysisQuery>,
) -> Result<Json<Vec<WebsiteAnalysis>>, StatusCode> {
    let start_time = std::time::Instant::now();
    let limit = query.limit.unwrap_or(10);
    
    info!("📋 Getting analyses - URL filter: {:?}, limit: {}", query.url, limit);
    
    match state.db_pool.get_analyses(query.url.as_deref(), limit).await {
        Ok(analyses) => {
            let duration = start_time.elapsed();
            info!("✅ Retrieved {} analyses from database (took {:?})", analyses.len(), duration);
            Ok(Json(analyses))
        },
        Err(e) => {
            let duration = start_time.elapsed();
            error!("❌ Failed to get analyses after {:?}: {}", duration, e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_analysis_by_id(
    State(state): State<AppState>,
    axum::extract::Path(id): axum::extract::Path<Uuid>,
) -> Result<Json<WebsiteAnalysis>, StatusCode> {
    let start_time = std::time::Instant::now();
    info!("🔍 Getting analysis by ID: {}", id);
    
    match state.db_pool.get_analysis_by_id(id).await {
        Ok(Some(analysis)) => {
            let duration = start_time.elapsed();
            info!("✅ Found analysis {} for URL: {} (took {:?})", id, analysis.url, duration);
            Ok(Json(analysis))
        },
        Ok(None) => {
            let duration = start_time.elapsed();
            warn!("⚠️  Analysis not found: {} (took {:?})", id, duration);
            Err(StatusCode::NOT_FOUND)
        },
        Err(e) => {
            let duration = start_time.elapsed();
            error!("❌ Failed to get analysis {} after {:?}: {}", id, duration, e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}