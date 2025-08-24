use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tracing::{info, error};
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

#[derive(Debug, Deserialize)]
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
        .unwrap_or_else(|_| "postgresql://qa_user:qa_password@localhost:5432/qa_automation".to_string());
    
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
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3001").await?;
    info!("Website Analyzer service starting on port 3001");

    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check() -> &'static str {
    "Website Analyzer Service is healthy"
}

async fn analyze_website(
    State(state): State<AppState>,
    Json(request): Json<AnalyzeRequest>,
) -> Result<Json<AnalyzeResponse>, StatusCode> {
    info!("Analyzing website: {}", request.url);

    match state.analyzer.analyze(&request.url).await {
        Ok(analysis) => {
            let analysis_id = analysis.analysis_id;
            
            // Store analysis in database
            if let Err(e) = state.db_pool.store_analysis(&analysis).await {
                error!("Failed to store analysis: {}", e);
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }

            info!("Analysis completed for {}: {}", request.url, analysis_id);

            Ok(Json(AnalyzeResponse {
                analysis_id,
                analysis,
            }))
        }
        Err(e) => {
            error!("Analysis failed for {}: {}", request.url, e);
            Err(StatusCode::BAD_REQUEST)
        }
    }
}

async fn get_analyses(
    State(state): State<AppState>,
    Query(query): Query<GetAnalysisQuery>,
) -> Result<Json<Vec<WebsiteAnalysis>>, StatusCode> {
    let limit = query.limit.unwrap_or(10);
    
    match state.db_pool.get_analyses(query.url.as_deref(), limit).await {
        Ok(analyses) => Ok(Json(analyses)),
        Err(e) => {
            error!("Failed to get analyses: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_analysis_by_id(
    State(state): State<AppState>,
    axum::extract::Path(id): axum::extract::Path<Uuid>,
) -> Result<Json<WebsiteAnalysis>, StatusCode> {
    match state.db_pool.get_analysis_by_id(id).await {
        Ok(Some(analysis)) => Ok(Json(analysis)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            error!("Failed to get analysis: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}