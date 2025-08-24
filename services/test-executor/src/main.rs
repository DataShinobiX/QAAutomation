use axum::{
    extract::{State, Path},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use tower_http::cors::CorsLayer;
use tracing::{info, error};
use uuid::Uuid;

pub mod executor;
pub mod runner;
pub mod browser;
pub mod models;

use executor::TestExecutor;
use models::{TestSuite, TestExecution, ExecutionConfig};

#[derive(Clone)]
pub struct AppState {
    executor: TestExecutor,
}

#[derive(Debug, Deserialize)]
pub struct ExecuteTestSuiteRequest {
    test_suite: TestSuite,
}

#[derive(Debug, Serialize)]
pub struct ExecuteTestSuiteResponse {
    execution: TestExecution,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .init();

    // Load environment variables
    dotenvy::dotenv().ok();

    // Initialize test executor with default config
    let config = ExecutionConfig::default();
    let executor = TestExecutor::new(config);

    // Create application state
    let state = AppState { executor };

    // Build our application with routes
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/execute", post(execute_test_suite))
        .route("/executions/:id", get(get_execution_by_id))
        .route("/config", get(get_config))
        .route("/config", post(update_config))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3003").await?;
    info!("Test Executor service starting on port 3003");

    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check() -> &'static str {
    "Test Executor Service is healthy"
}

async fn execute_test_suite(
    State(state): State<AppState>,
    Json(request): Json<ExecuteTestSuiteRequest>,
) -> Result<Json<ExecuteTestSuiteResponse>, StatusCode> {
    info!("Executing test suite: {}", request.test_suite.name);

    match state.executor.execute_test_suite(request.test_suite).await {
        Ok(execution) => {
            info!("Test suite execution completed: {}", execution.id);
            Ok(Json(ExecuteTestSuiteResponse { execution }))
        }
        Err(e) => {
            error!("Test suite execution failed: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn get_execution_by_id(
    State(_state): State<AppState>,
    Path(_execution_id): Path<Uuid>,
) -> Result<Json<TestExecution>, StatusCode> {
    // In a real implementation, this would load from database
    error!("Get execution by ID not implemented - requires database integration");
    Err(StatusCode::NOT_IMPLEMENTED)
}

async fn get_config(
    State(state): State<AppState>,
) -> Json<ExecutionConfig> {
    Json(state.executor.get_config().clone())
}

#[derive(Debug, Deserialize)]
pub struct UpdateConfigRequest {
    config: ExecutionConfig,
}

async fn update_config(
    State(mut state): State<AppState>,
    Json(request): Json<UpdateConfigRequest>,
) -> Result<Json<ExecutionConfig>, StatusCode> {
    info!("Updating test executor configuration");
    
    state.executor.update_config(request.config);
    Ok(Json(state.executor.get_config().clone()))
}