use anyhow::{Context, Result};
use aws_sdk_s3::{Client, primitives::ByteStream};
use chrono::Utc;
use image::DynamicImage;
use shared::{Screenshot, Viewport, ImageFormat, VisualTest, VisualComparison};
use std::fs;
use std::path::Path;
use tracing::{debug, info};
use uuid::Uuid;

#[derive(Clone)]
pub struct StorageManager {
    s3_client: Client,
    bucket_name: String,
}

impl StorageManager {
    pub async fn new() -> Result<Self> {
        info!("Initializing storage manager with MinIO/S3...");

        // Load configuration from environment
        let endpoint_url = std::env::var("MINIO_ENDPOINT")
            .unwrap_or_else(|_| "http://localhost:9000".to_string());
        let access_key = std::env::var("MINIO_ACCESS_KEY")
            .unwrap_or_else(|_| "minioadmin".to_string());
        let secret_key = std::env::var("MINIO_SECRET_KEY")
            .unwrap_or_else(|_| "minioadmin123".to_string());
        let bucket_name = std::env::var("MINIO_BUCKET")
            .unwrap_or_else(|_| "qa-automation-artifacts".to_string());

        info!("MinIO Configuration:");
        info!("  - Endpoint: {}", endpoint_url);
        info!("  - Access Key: {}", access_key);
        info!("  - Bucket: {}", bucket_name);

        // Disable IMDS (Instance Metadata Service) which can cause timeouts
        std::env::set_var("AWS_EC2_METADATA_DISABLED", "true");
        std::env::set_var("AWS_REGION", "us-east-1");
        
        // Configure AWS SDK for MinIO with explicit settings
        let config = aws_config::defaults(aws_config::BehaviorVersion::latest())
            .region("us-east-1")  // Fixed region for MinIO
            .endpoint_url(&endpoint_url)
            .credentials_provider(aws_sdk_s3::config::Credentials::new(
                access_key,
                secret_key,
                None,
                None,
                "minio",
            ))
            .load()
            .await;

        // Create S3 client with additional configuration
        let s3_config = aws_sdk_s3::Config::from(&config);
        let s3_client = Client::from_conf(s3_config);

        // Ensure bucket exists
        let storage_manager = Self {
            s3_client,
            bucket_name,
        };

        // Test basic connectivity first
        info!("Testing S3 client connectivity...");
        match storage_manager.test_connectivity().await {
            Ok(_) => {
                info!("S3 connectivity test passed");
            }
            Err(e) => {
                info!("S3 connectivity test failed: {} - continuing with local storage only", e);
                // Don't return error, continue with local storage
            }
        }

        match storage_manager.ensure_bucket_exists().await {
            Ok(_) => {
                info!("Storage manager initialized successfully with MinIO");
                Ok(storage_manager)
            }
            Err(e) => {
                info!("MinIO storage not available: {} - continuing with local storage only", e);
                // Still return the storage manager for local screenshots
                Ok(storage_manager)
            }
        }
    }

    async fn test_connectivity(&self) -> Result<()> {
        info!("Testing basic S3 connectivity...");
        
        // Try to list buckets as a connectivity test
        match self.s3_client.list_buckets().send().await {
            Ok(_) => {
                debug!("S3 list_buckets call successful");
                Ok(())
            }
            Err(e) => {
                debug!("S3 connectivity test failed: {}", e);
                Err(anyhow::anyhow!("S3 connectivity failed: {}", e))
            }
        }
    }

    async fn ensure_bucket_exists(&self) -> Result<()> {
        debug!("Checking if bucket '{}' exists", self.bucket_name);
        
        // Try to list objects in the bucket as a simpler test
        match self.s3_client
            .list_objects_v2()
            .bucket(&self.bucket_name)
            .max_keys(1)
            .send()
            .await
        {
            Ok(_) => {
                debug!("Bucket '{}' accessible", self.bucket_name);
                Ok(())
            }
            Err(err) => {
                debug!("Bucket access failed: {}, attempting to create", err);
                info!("Creating bucket '{}'", self.bucket_name);
                
                match self.s3_client
                    .create_bucket()
                    .bucket(&self.bucket_name)
                    .send()
                    .await
                {
                    Ok(_) => {
                        info!("Bucket '{}' created successfully", self.bucket_name);
                        Ok(())
                    }
                    Err(create_err) => {
                        let err_str = create_err.to_string();
                        // Check if it's because the bucket already exists
                        if err_str.contains("BucketAlreadyExists") 
                            || err_str.contains("BucketAlreadyOwnedByYou") 
                            || err_str.contains("already exists") {
                            debug!("Bucket already exists (from create error)");
                            Ok(())
                        } else {
                            Err(create_err).context("Failed to create bucket")
                        }
                    }
                }
            }
        }
    }

    pub async fn store_screenshot(
        &self,
        screenshot_data: Vec<u8>,
        viewport: &Viewport,
        url: &str,
    ) -> Result<Screenshot> {
        let screenshot_id = Uuid::new_v4();
        let timestamp = Utc::now();
        
        // Create file path
        let file_path = format!(
            "screenshots/{}/{}/{}x{}/{}.png",
            timestamp.format("%Y/%m/%d"),
            self.sanitize_url(url),
            viewport.width,
            viewport.height,
            screenshot_id
        );

        debug!("Storing screenshot at path: {}", file_path);

        // Save screenshot locally first
        self.save_screenshot_locally(&screenshot_data, &file_path)
            .await
            .context("Failed to save screenshot locally")?;

        // Upload to MinIO/S3 (optional - skip if MinIO is not available)
        match self.s3_client
            .put_object()
            .bucket(&self.bucket_name)
            .key(&file_path)
            .body(ByteStream::from(screenshot_data.clone()))
            .content_type("image/png")
            .send()
            .await
        {
            Ok(_) => info!("Screenshot uploaded to MinIO successfully"),
            Err(e) => {
                info!("MinIO upload failed (continuing with local only): {}", e);
                // Continue without MinIO - local screenshot is still saved
            }
        }

        // Get image dimensions
        let image = image::load_from_memory(&screenshot_data)
            .context("Failed to load screenshot for dimension detection")?;

        let screenshot = Screenshot {
            id: screenshot_id,
            viewport: viewport.clone(),
            file_path: file_path.clone(),
            file_size: screenshot_data.len() as u64,
            width: image.width(),
            height: image.height(),
            format: ImageFormat::PNG,
            created_at: timestamp,
        };

        info!("Screenshot stored successfully: {} ({}x{}) - Local: screenshots/{}", 
              screenshot_id, image.width(), image.height(), file_path);
        Ok(screenshot)
    }

    pub async fn store_diff_image(
        &self,
        diff_image: DynamicImage,
        baseline_id: Uuid,
        current_id: Uuid,
    ) -> Result<String> {
        let timestamp = Utc::now();
        let file_path = format!(
            "diffs/{}/{}_vs_{}.png",
            timestamp.format("%Y/%m/%d"),
            baseline_id,
            current_id
        );

        debug!("Storing diff image at path: {}", file_path);

        // Convert image to PNG bytes
        let mut png_data = Vec::new();
        diff_image
            .write_to(&mut std::io::Cursor::new(&mut png_data), image::ImageFormat::Png)
            .context("Failed to encode diff image as PNG")?;

        // Save diff image locally first
        self.save_screenshot_locally(&png_data, &file_path)
            .await
            .context("Failed to save diff image locally")?;

        // Upload to MinIO/S3
        self.s3_client
            .put_object()
            .bucket(&self.bucket_name)
            .key(&file_path)
            .body(ByteStream::from(png_data))
            .content_type("image/png")
            .send()
            .await
            .context("Failed to upload diff image to storage")?;

        info!("Diff image stored successfully: {}", file_path);
        Ok(format!("http://localhost:9000/{}/{}", self.bucket_name, file_path))
    }

    pub async fn get_screenshot_data(&self, screenshot_id: Uuid) -> Result<Vec<u8>> {
        // First, find the screenshot metadata to get the file path
        // For now, we'll construct the path - in production you'd query the database
        // This is a simplified version for demo purposes
        
        // Try common paths
        let possible_paths = vec![
            format!("screenshots/**/*/{}.png", screenshot_id),
        ];

        for _path_pattern in possible_paths {
            if let Ok(objects) = self.list_objects_with_prefix(&format!("screenshots/")).await {
                for object in objects {
                    if object.contains(&screenshot_id.to_string()) {
                        return self.get_object_data(&object).await;
                    }
                }
            }
        }

        Err(anyhow::anyhow!("Screenshot not found: {}", screenshot_id))
    }

    async fn get_object_data(&self, key: &str) -> Result<Vec<u8>> {
        let response = self.s3_client
            .get_object()
            .bucket(&self.bucket_name)
            .key(key)
            .send()
            .await
            .context("Failed to get object from storage")?;

        let data = response.body.collect().await
            .context("Failed to read object data")?;

        Ok(data.into_bytes().to_vec())
    }

    async fn list_objects_with_prefix(&self, prefix: &str) -> Result<Vec<String>> {
        let response = self.s3_client
            .list_objects_v2()
            .bucket(&self.bucket_name)
            .prefix(prefix)
            .send()
            .await
            .context("Failed to list objects")?;

        let keys = response.contents()
            .iter()
            .flat_map(|obj| obj.key().map(|k| k.to_string()))
            .collect();

        Ok(keys)
    }

    pub async fn get_screenshot(&self, id: Uuid) -> Result<Option<Screenshot>> {
        // In a real implementation, this would query the database
        // For now, return None as we don't have database integration yet
        debug!("Getting screenshot metadata for ID: {}", id);
        Ok(None)
    }

    pub async fn get_visual_tests(&self, limit: i32) -> Result<Vec<VisualTest>> {
        // In a real implementation, this would query the database
        debug!("Getting visual tests (limit: {})", limit);
        Ok(Vec::new())
    }

    pub async fn get_visual_test(&self, id: Uuid) -> Result<Option<VisualTest>> {
        // In a real implementation, this would query the database
        debug!("Getting visual test for ID: {}", id);
        Ok(None)
    }

    pub async fn store_comparison(&self, comparison: &VisualComparison) -> Result<()> {
        // In a real implementation, this would store in the database
        info!("Storing comparison result: {} ({:.2}% difference)", 
              comparison.id, comparison.difference_percentage);
        Ok(())
    }

    async fn save_screenshot_locally(&self, screenshot_data: &[u8], file_path: &str) -> Result<()> {
        // Create local screenshots directory in the project root
        let local_path = file_path.to_string();
        let full_path = Path::new(&local_path);
        
        // Create parent directories if they don't exist
        if let Some(parent) = full_path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create local screenshot directories")?;
        }
        
        // Write the screenshot data to local file
        fs::write(&local_path, screenshot_data)
            .context("Failed to write screenshot to local file")?;
        
        info!("Screenshot saved locally: {}", local_path);
        Ok(())
    }

    fn sanitize_url(&self, url: &str) -> String {
        url.replace("https://", "")
            .replace("http://", "")
            .replace("/", "_")
            .replace("?", "_")
            .replace("&", "_")
            .replace("=", "_")
            .chars()
            .filter(|c| c.is_alphanumeric() || *c == '_' || *c == '-' || *c == '.')
            .collect()
    }
}