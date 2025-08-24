#!/bin/bash

echo "🔧 Setting up WebDriver for Visual Engine..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

echo "📱 Detected OS: $OS"

# Check if Chrome is installed
if command -v google-chrome >/dev/null 2>&1; then
    CHROME_CMD="google-chrome"
elif command -v chromium >/dev/null 2>&1; then
    CHROME_CMD="chromium"
elif command -v chromium-browser >/dev/null 2>&1; then
    CHROME_CMD="chromium-browser"  
elif [[ "$OS" == "macos" ]] && [ -d "/Applications/Google Chrome.app" ]; then
    CHROME_CMD="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
    echo "❌ Chrome/Chromium not found. Please install Chrome first:"
    if [[ "$OS" == "macos" ]]; then
        echo "   brew install --cask google-chrome"
    else
        echo "   sudo apt-get install google-chrome-stable"
    fi
    exit 1
fi

echo "✅ Found Chrome: $CHROME_CMD"

# Get Chrome version
if [[ "$OS" == "macos" ]]; then
    CHROME_VERSION=$("$CHROME_CMD" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
else
    CHROME_VERSION=$($CHROME_CMD --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
fi

if [ -z "$CHROME_VERSION" ]; then
    echo "❌ Could not detect Chrome version"
    exit 1
fi

echo "🌐 Chrome version: $CHROME_VERSION"

# Extract major version
CHROME_MAJOR=$(echo $CHROME_VERSION | cut -d. -f1)
echo "📊 Chrome major version: $CHROME_MAJOR"

# Check if ChromeDriver is already installed and correct version
if command -v chromedriver >/dev/null 2>&1; then
    EXISTING_VERSION=$(chromedriver --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    EXISTING_MAJOR=$(echo $EXISTING_VERSION | cut -d. -f1)
    
    if [ "$EXISTING_MAJOR" = "$CHROME_MAJOR" ]; then
        echo "✅ ChromeDriver $EXISTING_VERSION already installed and compatible"
        echo "🚀 Starting ChromeDriver on port 4444..."
        chromedriver --port=4444 &
        CHROMEDRIVER_PID=$!
        echo "📝 ChromeDriver PID: $CHROMEDRIVER_PID"
        echo "⏳ Waiting for ChromeDriver to start..."
        sleep 3
        echo "✅ ChromeDriver should be running at http://localhost:4444"
        echo "🛑 To stop: kill $CHROMEDRIVER_PID"
        exit 0
    else
        echo "⚠️  ChromeDriver version mismatch. Need version $CHROME_MAJOR.x, have $EXISTING_VERSION"
    fi
fi

echo "📥 Installing ChromeDriver..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Download appropriate ChromeDriver
if [[ "$OS" == "macos" ]]; then
    if [[ $(uname -m) == "arm64" ]]; then
        PLATFORM="mac-arm64"
    else
        PLATFORM="mac-x64"
    fi
else
    PLATFORM="linux64"
fi

# Get latest ChromeDriver version for this Chrome major version
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}")

if [ -z "$CHROMEDRIVER_VERSION" ]; then
    echo "❌ Could not find ChromeDriver for Chrome $CHROME_MAJOR"
    echo "💡 Try updating Chrome or check https://chromedriver.chromium.org/"
    exit 1
fi

echo "📦 Downloading ChromeDriver $CHROMEDRIVER_VERSION for $PLATFORM..."

DOWNLOAD_URL="https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_${PLATFORM}.zip"

curl -L -o chromedriver.zip "$DOWNLOAD_URL"

if [ $? -ne 0 ]; then
    echo "❌ Failed to download ChromeDriver"
    exit 1
fi

# Extract and install
unzip -q chromedriver.zip

if [[ "$OS" == "macos" ]]; then
    # Remove quarantine attribute on macOS
    xattr -d com.apple.quarantine chromedriver 2>/dev/null || true
    # Install to /usr/local/bin
    sudo mv chromedriver /usr/local/bin/
else
    # Install to /usr/local/bin on Linux
    sudo mv chromedriver /usr/local/bin/
fi

sudo chmod +x /usr/local/bin/chromedriver

# Clean up
cd /
rm -rf "$TEMP_DIR"

echo "✅ ChromeDriver $CHROMEDRIVER_VERSION installed successfully"

# Test installation
INSTALLED_VERSION=$(chromedriver --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
echo "🧪 Installed ChromeDriver version: $INSTALLED_VERSION"

# Start ChromeDriver
echo "🚀 Starting ChromeDriver on port 4444..."
chromedriver --port=4444 &
CHROMEDRIVER_PID=$!

echo "📝 ChromeDriver PID: $CHROMEDRIVER_PID"
echo "⏳ Waiting for ChromeDriver to start..."
sleep 3

# Test connection
if curl -s http://localhost:4444/status >/dev/null; then
    echo "✅ ChromeDriver is running at http://localhost:4444"
    echo "🎯 Visual Engine can now capture real screenshots!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Set environment variable: export WEBDRIVER_URL=http://localhost:4444"
    echo "   2. Run Visual Engine: cargo run --bin visual-engine"
    echo "   3. Test with: curl -X POST http://localhost:3002/capture -d '{\"url\":\"https://example.com\"}'"
    echo ""
    echo "🛑 To stop ChromeDriver: kill $CHROMEDRIVER_PID"
else
    echo "❌ ChromeDriver failed to start properly"
    kill $CHROMEDRIVER_PID 2>/dev/null
    exit 1
fi