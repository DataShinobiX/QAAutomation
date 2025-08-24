use anyhow::{Context, Result};
use chrono::Utc;
use image::{DynamicImage, ImageBuffer, Rgb, RgbImage};
use shared::VisualComparison;
use tracing::{debug, info};
use uuid::Uuid;

use crate::storage::StorageManager;

#[derive(Clone)]
pub struct ImageComparator {
    // Configuration for comparison
    pixel_threshold: u8,      // Threshold for individual pixel differences (0-255)
    ignore_antialiasing: bool, // Whether to ignore minor antialiasing differences
}

impl ImageComparator {
    pub fn new() -> Self {
        Self {
            pixel_threshold: 10,      // Allow small differences in pixel values
            ignore_antialiasing: true,
        }
    }

    pub fn with_config(pixel_threshold: u8, ignore_antialiasing: bool) -> Self {
        Self {
            pixel_threshold,
            ignore_antialiasing,
        }
    }

    pub async fn compare_screenshots(
        &self,
        baseline_id: Uuid,
        current_id: Uuid,
        difference_threshold: f64,
        storage: &StorageManager,
    ) -> Result<VisualComparison> {
        info!("Starting screenshot comparison: {} vs {}", baseline_id, current_id);

        // Load both screenshots
        let baseline_data = storage.get_screenshot_data(baseline_id).await
            .context("Failed to load baseline screenshot")?;
        let current_data = storage.get_screenshot_data(current_id).await
            .context("Failed to load current screenshot")?;

        // Load images
        let baseline_img = image::load_from_memory(&baseline_data)
            .context("Failed to decode baseline image")?;
        let current_img = image::load_from_memory(&current_data)
            .context("Failed to decode current image")?;

        // Ensure images have the same dimensions
        let (baseline_img, current_img) = self.normalize_dimensions(baseline_img, current_img)?;

        // Perform pixel-by-pixel comparison
        let comparison_result = self.compare_images(&baseline_img, &current_img)?;

        // Calculate difference percentage
        let total_pixels = (baseline_img.width() * baseline_img.height()) as u64;
        let difference_percentage = (comparison_result.different_pixels as f64 / total_pixels as f64) * 100.0;

        let passed = difference_percentage <= difference_threshold;

        // Create difference image if there are differences
        let diff_image_path = if comparison_result.different_pixels > 0 {
            let diff_img = self.create_difference_image(&baseline_img, &current_img, &comparison_result.diff_mask)?;
            Some(storage.store_diff_image(diff_img, baseline_id, current_id).await?)
        } else {
            None
        };

        let comparison = VisualComparison {
            id: Uuid::new_v4(),
            baseline_screenshot_id: baseline_id,
            current_screenshot_id: current_id,
            difference_percentage,
            different_pixels: comparison_result.different_pixels,
            total_pixels,
            diff_image_path,
            passed,
            threshold: difference_threshold,
            created_at: Utc::now(),
        };

        info!(
            "Screenshot comparison completed: {:.2}% difference ({} pixels), passed: {}",
            difference_percentage,
            comparison_result.different_pixels,
            passed
        );

        // Store comparison result
        storage.store_comparison(&comparison).await?;

        Ok(comparison)
    }

    fn normalize_dimensions(&self, img1: DynamicImage, img2: DynamicImage) -> Result<(DynamicImage, DynamicImage)> {
        let (w1, h1) = (img1.width(), img1.height());
        let (w2, h2) = (img2.width(), img2.height());

        if w1 == w2 && h1 == h2 {
            return Ok((img1, img2));
        }

        debug!("Normalizing image dimensions: {}x{} and {}x{}", w1, h1, w2, h2);

        // Use the smaller dimensions to crop both images
        let target_width = w1.min(w2);
        let target_height = h1.min(h2);

        let normalized_img1 = img1.crop_imm(0, 0, target_width, target_height);
        let normalized_img2 = img2.crop_imm(0, 0, target_width, target_height);

        Ok((normalized_img1, normalized_img2))
    }

    fn compare_images(&self, img1: &DynamicImage, img2: &DynamicImage) -> Result<ComparisonResult> {
        let rgb1 = img1.to_rgb8();
        let rgb2 = img2.to_rgb8();

        let (width, height) = (rgb1.width(), rgb1.height());
        let mut different_pixels = 0u64;
        let mut diff_mask = ImageBuffer::new(width, height);

        // Compare pixel by pixel
        for y in 0..height {
            for x in 0..width {
                let pixel1 = rgb1.get_pixel(x, y);
                let pixel2 = rgb2.get_pixel(x, y);

                let is_different = if self.ignore_antialiasing {
                    self.is_pixel_significantly_different(pixel1, pixel2, x, y, &rgb1, &rgb2)
                } else {
                    self.is_pixel_different(pixel1, pixel2)
                };

                if is_different {
                    different_pixels += 1;
                    // Mark difference in red
                    diff_mask.put_pixel(x, y, Rgb([255, 0, 0]));
                } else {
                    // Keep original pixel but dimmed
                    let orig = rgb1.get_pixel(x, y);
                    diff_mask.put_pixel(x, y, Rgb([
                        (orig[0] as f32 * 0.7) as u8,
                        (orig[1] as f32 * 0.7) as u8,
                        (orig[2] as f32 * 0.7) as u8,
                    ]));
                }
            }
        }

        Ok(ComparisonResult {
            different_pixels,
            diff_mask,
        })
    }

    fn is_pixel_different(&self, pixel1: &Rgb<u8>, pixel2: &Rgb<u8>) -> bool {
        let threshold = self.pixel_threshold as i16;
        
        for i in 0..3 {
            let diff = (pixel1[i] as i16 - pixel2[i] as i16).abs();
            if diff > threshold {
                return true;
            }
        }
        false
    }

    fn is_pixel_significantly_different(
        &self,
        pixel1: &Rgb<u8>,
        pixel2: &Rgb<u8>,
        x: u32,
        y: u32,
        img1: &RgbImage,
        img2: &RgbImage,
    ) -> bool {
        // First check basic pixel difference
        if !self.is_pixel_different(pixel1, pixel2) {
            return false;
        }

        // If ignore_antialiasing is enabled, check surrounding pixels
        // to see if this might be antialiasing
        if self.ignore_antialiasing {
            let antialiasing_score = self.calculate_antialiasing_score(x, y, img1, img2);
            // If this looks like antialiasing, don't count it as a significant difference
            if antialiasing_score > 0.7 {
                return false;
            }
        }

        true
    }

    fn calculate_antialiasing_score(&self, x: u32, y: u32, img1: &RgbImage, img2: &RgbImage) -> f32 {
        let (width, height) = (img1.width(), img1.height());
        let mut similar_neighbors = 0;
        let mut total_neighbors = 0;

        // Check 3x3 neighborhood
        for dy in -1i32..=1 {
            for dx in -1i32..=1 {
                if dx == 0 && dy == 0 {
                    continue; // Skip center pixel
                }

                let nx = x as i32 + dx;
                let ny = y as i32 + dy;

                if nx >= 0 && ny >= 0 && nx < width as i32 && ny < height as i32 {
                    let neighbor1 = img1.get_pixel(nx as u32, ny as u32);
                    let neighbor2 = img2.get_pixel(nx as u32, ny as u32);

                    total_neighbors += 1;
                    if !self.is_pixel_different(neighbor1, neighbor2) {
                        similar_neighbors += 1;
                    }
                }
            }
        }

        if total_neighbors == 0 {
            return 0.0;
        }

        similar_neighbors as f32 / total_neighbors as f32
    }

    fn create_difference_image(
        &self,
        baseline: &DynamicImage,
        current: &DynamicImage,
        diff_mask: &RgbImage,
    ) -> Result<DynamicImage> {
        // Create a side-by-side comparison image
        let (width, height) = (baseline.width(), baseline.height());
        let mut comparison_img = ImageBuffer::new(width * 3, height);

        let baseline_rgb = baseline.to_rgb8();
        let current_rgb = current.to_rgb8();

        // Left: baseline image
        for y in 0..height {
            for x in 0..width {
                let pixel = baseline_rgb.get_pixel(x, y);
                comparison_img.put_pixel(x, y, *pixel);
            }
        }

        // Middle: current image
        for y in 0..height {
            for x in 0..width {
                let pixel = current_rgb.get_pixel(x, y);
                comparison_img.put_pixel(x + width, y, *pixel);
            }
        }

        // Right: difference mask
        for y in 0..height {
            for x in 0..width {
                let pixel = diff_mask.get_pixel(x, y);
                comparison_img.put_pixel(x + width * 2, y, *pixel);
            }
        }

        Ok(DynamicImage::ImageRgb8(comparison_img))
    }
}

struct ComparisonResult {
    different_pixels: u64,
    diff_mask: RgbImage,
}