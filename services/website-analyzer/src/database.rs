use anyhow::{Context, Result};
use shared::WebsiteAnalysis;
use sqlx::{PgPool, Row};
use tracing::{debug, error};
use uuid::Uuid;

#[derive(Clone)]
pub struct DatabasePool {
    pool: PgPool,
}

impl DatabasePool {
    pub async fn new(database_url: &str) -> Result<Self> {
        use sqlx::postgres::PgPoolOptions;
        
        let pool = PgPoolOptions::new()
            .max_connections(10)
            .acquire_timeout(std::time::Duration::from_secs(30))
            .connect(database_url)
            .await
            .context("Failed to connect to database")?;

        Ok(Self { pool })
    }

    pub async fn store_analysis(&self, analysis: &WebsiteAnalysis) -> Result<()> {
        let analysis_json = serde_json::to_value(analysis)
            .context("Failed to serialize analysis to JSON")?;

        sqlx::query(
            r#"
            INSERT INTO website_analyses (id, url, analysis_data)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET
                analysis_data = EXCLUDED.analysis_data,
                updated_at = NOW()
            "#,
        )
        .bind(analysis.analysis_id)
        .bind(&analysis.url)
        .bind(analysis_json)
        .execute(&self.pool)
        .await
        .context("Failed to store analysis in database")?;

        debug!("Stored analysis {} for URL: {}", analysis.analysis_id, analysis.url);
        Ok(())
    }

    pub async fn get_analysis_by_id(&self, id: Uuid) -> Result<Option<WebsiteAnalysis>> {
        let row = sqlx::query("SELECT analysis_data FROM website_analyses WHERE id = $1")
            .bind(id)
            .fetch_optional(&self.pool)
            .await
            .context("Failed to fetch analysis from database")?;

        match row {
            Some(row) => {
                let analysis_data: serde_json::Value = row.get("analysis_data");
                let analysis: WebsiteAnalysis = serde_json::from_value(analysis_data)
                    .context("Failed to deserialize analysis from database")?;
                Ok(Some(analysis))
            }
            None => Ok(None),
        }
    }

    pub async fn get_analyses(&self, url_filter: Option<&str>, limit: i64) -> Result<Vec<WebsiteAnalysis>> {
        let rows = match url_filter {
            Some(url) => {
                sqlx::query("SELECT analysis_data FROM website_analyses WHERE url = $1 ORDER BY created_at DESC LIMIT $2")
                    .bind(url)
                    .bind(limit)
                    .fetch_all(&self.pool)
                    .await
                    .context("Failed to fetch analyses from database")?
            }
            None => {
                sqlx::query("SELECT analysis_data FROM website_analyses ORDER BY created_at DESC LIMIT $1")
                    .bind(limit)
                    .fetch_all(&self.pool)
                    .await
                    .context("Failed to fetch analyses from database")?
            }
        };

        let mut analyses = Vec::new();
        for row in rows {
            let analysis_data: serde_json::Value = row.get("analysis_data");
            match serde_json::from_value::<WebsiteAnalysis>(analysis_data) {
                Ok(analysis) => analyses.push(analysis),
                Err(e) => {
                    error!("Failed to deserialize analysis from database: {}", e);
                    // Continue with other analyses instead of failing completely
                    continue;
                }
            }
        }

        Ok(analyses)
    }

    pub async fn health_check(&self) -> Result<()> {
        sqlx::query("SELECT 1")
            .fetch_one(&self.pool)
            .await
            .context("Database health check failed")?;
        Ok(())
    }
}