# LexiQA Frontend MVP

A React-based frontend for the LexiQA QA automation platform.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Features

### 1. Test Configuration
- Website URL input with validation
- Optional login credentials for protected sites
- Figma file key input for design comparison
- Workflow type selection (Quick/Full Analysis)
- Real-time service health monitoring

### 2. Workflow Progress
- Real-time progress tracking with step-by-step updates
- Service health status indicators
- Progress bar with estimated completion time
- Detailed workflow steps visualization

### 3. Results Dashboard
- **Overview Tab:** Execution summary and metrics
- **Test Cases Tab:** Generated AI test cases by category
- **Design Comparison Tab:** Figma vs implementation analysis
- **Execution Results Tab:** Browser test execution results
- **Service Status Tab:** Microservices health and execution timeline

## Backend Integration

The frontend connects to the LexiQA backend services:
- **Workflow Orchestrator (Port 8008):** Main coordination service
- Automatically polls for workflow status updates every 2 seconds
- Real-time service health monitoring every 30 seconds

## Usage Flow

1. **Configure Test:** Enter website URL, credentials (if needed), and Figma file key
2. **Monitor Progress:** Watch real-time progress as the platform analyzes your website
3. **View Results:** Explore comprehensive test results, design comparisons, and execution outcomes

## Environment Requirements

- Backend services must be running (see main project README)
- Workflow Orchestrator must be accessible at `http://localhost:8008`
- Modern web browser with JavaScript enabled

## Technology Stack

- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **Axios** for API communication
- **Lucide React** for icons
- **Vite** for development and building