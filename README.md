# REAIC - Real Estate AI Consultant

A Docker-based AI application for real estate consulting, providing property valuation, market analysis, and investment strategies.

## Prerequisites

- Docker Desktop installed on your machine
- Git installed on your machine

## Quick Start

1. Clone this repository:
```bash
git clone <your-github-repo-url>
cd REAIC
```

2. Create a `.env` file in the root directory with your API keys:
```
FLASK_SECRET_KEY=your-secret-key
GROQ_API_KEY=your-groq-api-key
```

3. Build the Docker image:
```bash
docker build -t reaic-app .
```

4. Run the container:
```bash
docker run -d -p 5000:5000 --env-file .env -v "$(pwd)/pdf_files:/app/pdf_files" -v "$(pwd)/vector_db:/app/vector_db" -v "$(pwd)/chat_history:/app/chat_history" reaic-app
```

5. Access the application at: http://localhost:5000

## Features

- Real-time AI chat interface
- Document processing and analysis
- Property valuation assistance
- Market analysis
- Investment strategy consulting
- Transaction negotiation support

## Usage

1. Open your web browser and navigate to http://localhost:5000
2. Upload relevant PDF documents using the interface
3. Start chatting with the AI consultant about your real estate queries

## Stopping the Container

To stop the container:
```bash
docker ps  # Find the container ID
docker stop <container-id>
```

## Troubleshooting

If you can't access the application:
1. Make sure Docker Desktop is running
2. Check if port 5000 is available on your machine
3. Verify that all environment variables are set correctly in the .env file
