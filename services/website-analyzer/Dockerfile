# Build stage
FROM rust:1.75 as builder

WORKDIR /app

# Copy workspace configuration
COPY Cargo.toml Cargo.lock ./

# Copy all service directories (needed for workspace)
COPY services/ ./services/

# Build the website-analyzer service
RUN cargo build --release --bin website-analyzer

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1001 app
USER app

WORKDIR /app

# Copy the built binary
COPY --from=builder /app/target/release/website-analyzer /app/website-analyzer

# Copy migration files (if any)
COPY --chown=app:app infrastructure/migrations ./migrations/

EXPOSE 3001

CMD ["./website-analyzer"]