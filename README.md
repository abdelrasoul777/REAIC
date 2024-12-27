# REAIC - Real Estate AI Consultant

A Docker-based AI application for real estate consulting, providing property valuation, market analysis, and investment strategies.

## Prerequisites

- Docker Desktop installed on your machine
- Git installed on your machine
- Groq API key (for AI language model)
- Nomic API token (for embeddings)

## Setting Up API Keys

1. Get your API keys:
   - Groq API Key:
     - Sign up at [Groq Console](https://console.groq.com)
     - Generate an API key from your dashboard
   
   - Nomic API Token:
     - Sign up at [Nomic Atlas](https://atlas.nomic.ai)
     - Get your API token from the dashboard

2. Create your environment file:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```

3. Edit the `.env` file with your actual keys:
   ```
   GROQ_API_KEY=gsk_your_actual_groq_key_here
   NOMIC_API_TOKEN=nk-your_actual_nomic_token_here
   FLASK_SECRET_KEY=any-random-string-for-security
   ```

   Notes:
   - GROQ_API_KEY: Must start with 'gsk_' (get this from Groq Console)
   - NOMIC_API_TOKEN: Must start with 'nk-' (get this from Nomic Atlas)
   - FLASK_SECRET_KEY: Can be any random string (used for session security)

## Quick Start

1. Clone this repository:
```bash
git clone <your-github-repo-url>
cd REAIC
```

2. Follow the "Setting Up API Keys" section above to create your `.env` file

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
3. Verify that all your API keys are correctly set in the .env file
4. Check Docker logs for any errors:
   ```bash
   docker logs <container-id>
   ```

## API Key Security

⚠️ Important Security Notes:
- Never commit your `.env` file to version control
- Keep your API keys confidential
- Regularly rotate your API keys for better security
- If you accidentally expose your API keys, regenerate them immediately
- Make sure your API keys have the correct format:
  - Groq key starts with 'gsk_'
  - Nomic token starts with 'nk-'
