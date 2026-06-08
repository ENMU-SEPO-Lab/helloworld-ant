# Hybrid GitHub Actions with Self-Hosted Runner and Ollama API Integration

## Overview

This project implements a **hybrid CI/CD pipeline** using GitHub Actions where:

- **Job 1 (Cloud)** runs on GitHub-hosted runners for:
  - Build
  - Unit tests (JUnit)
  - Code quality checks

- **Job 2 (Local Server)** runs on a self-hosted runner on an Ubuntu server for:
  - AI inference using Ollama
  - Local model execution
  - Experimentation and analysis tasks
  - Custom LLM API execution

This setup allows developers to combine the scalability of GitHub-hosted runners with the power of locally hosted LLMs running on private infrastructure.

---

# Architecture

```text
GitHub Push
    ↓
GitHub Actions Trigger
    ↓
--------------------------------
| Job 1 → GitHub VM           |
| Job 2 → Self-Hosted Server  |
--------------------------------
    ↓
Self-hosted runner executes Ollama locally
    ↓
FastAPI server communicates with Ollama
    ↓
Results returned to GitHub Actions
```

---

# Part 1 — Server Setup

## Step 1 — SSH into the Server

```bash
ssh your_user@your_server
```

Example:

```bash
ssh colab@10.243.109.249
```

---

## Step 2 — Install Basic Dependencies

```bash
sudo apt update
sudo apt install -y curl git python3 python3-pip python3-venv
```

---

## Step 3 — Install Ollama

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify installation:

```bash
ollama --version
```

---

## Step 4 — Start Ollama

Run Ollama server:

```bash
ollama serve
```

---

## Step 5 — Download a Model

Example using Phi-3.5:

```bash
ollama pull phi3.5
```

Optional additional models:

```bash
ollama pull mistral
ollama pull phi3
```

---

## Step 6 — Test Ollama Locally

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "phi3.5",
  "prompt": "hello",
  "stream": false
}'
```

You should receive a JSON response from the model.

---

# Part 2 — Create Python Environment

## Step 0 — Create and Activate Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Step 1 — Install Python Dependencies

```bash
pip install fastapi uvicorn requests
```

Verify installation:

```bash
python -m uvicorn --version
```

---

# Part 3 — Create the FastAPI LLM Server

Create a file named:

```text
server.py
```

Example implementation:

```python
from fastapi import FastAPI, Request, HTTPException
import requests

app = FastAPI()

API_KEY = "your_secret_key"

OLLAMA_URL = "http://localhost:11434/api/generate"

CREATE_MODEL = "phi3.5"
REVIEW_MODEL = "mistral"

def call_llm(model_name, prompt):
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    return response.json()

@app.post("/create")
async def create_code(request: Request):

    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()
    prompt = data.get("prompt")

    full_prompt = f"""
You are an expert software engineer.

Generate code only.
Do not provide explanations.
Do not use markdown.

Task:
{prompt}
"""

    result = call_llm(CREATE_MODEL, full_prompt)

    return {
        "response": result.get("response", "").strip()
    }

@app.post("/review")
async def review_code(request: Request):

    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()

    code = data.get("code")

    full_prompt = f"""
You are a senior software engineer.

Review the following code for:

- bugs
- readability
- performance
- edge cases
- security

Provide:
1. Explanation
2. Improved code

Code:
{code}
"""

    result = call_llm(REVIEW_MODEL, full_prompt)

    return {
        "response": result.get("response", "").strip()
    }
```

---

# Part 4 — Test the API Server

Run the server manually:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Open browser:

```text
http://YOUR_SERVER_IP:8000/docs
```

---

# Part 5 — Configure systemd Service

Create service file:

```bash
sudo nano /etc/systemd/system/llm-api.service
```

Paste:

```ini
[Unit]
Description=LLM FastAPI Server
After=network.target ollama.service
Requires=ollama.service

[Service]
User=colab
WorkingDirectory=/home/colab/workspace/exposed_ollama
ExecStart=/home/colab/workspace/exposed_ollama/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Important notes:

- `User` must match the Linux account running the project
- `WorkingDirectory` must point to the directory containing `server.py`
- `ExecStart` must point to the Python executable inside the virtual environment

---

## Reload and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable llm-api
sudo systemctl restart llm-api
```

Check status:

```bash
sudo systemctl status llm-api
```

View logs:

```bash
sudo journalctl -u llm-api -n 100 --no-pager
```

---

# Part 6 — Configure Ollama as a Service

Enable Ollama:

```bash
sudo systemctl enable ollama
sudo systemctl restart ollama
```

Check status:

```bash
sudo systemctl status ollama
```

Verify:

```bash
curl http://localhost:11434/api/tags
```

---

# Part 7 — Open Firewall

Allow external API access:

```bash
sudo ufw allow 8000
```

---

# Part 8 — Add HTTPS (Strongly Recommended)

Recommended options:

- Nginx + Let's Encrypt
- Cloudflare Tunnel

This prevents sending API traffic unencrypted over the network.

---

# Part 9 — Create GitHub Self-Hosted Runner

Navigate to:

```text
GitHub Repository
→ Settings
→ Actions
→ Runners
→ New self-hosted runner
```

Choose:

- Linux
- x64

---

## Download Runner

```bash
mkdir actions-runner && cd actions-runner

curl -o actions-runner.tar.gz -L \
https://github.com/actions/runner/releases/download/v2.333.1/actions-runner-linux-x64-2.333.1.tar.gz

tar xzf actions-runner.tar.gz
```

---

## Configure Runner

```bash
./config.sh --url https://github.com/YOUR_REPO --token YOUR_TOKEN
```

Recommended values:

- Runner group → ENTER
- Runner name → e.g. ollama-server
- Labels → optional
- Work folder → ENTER

---

## Start Runner

```bash
./run.sh
```

You should see:

```text
Listening for Jobs
```

---

## Install Runner as Service

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

Check status:

```bash
sudo ./svc.sh status
```

---

# Part 10 — GitHub Actions Workflow

Create:

```text
.github/workflows/ci.yml
```

Example workflow:

```yaml
name: Hybrid CI with Ollama

on:
  push:
    branches: [ main ]
  pull_request:

jobs:

  build:
    runs-on: ubuntu-latest

    steps:

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17

      - name: Install Ant
        run: |
          sudo apt-get update
          sudo apt-get install -y ant

      - name: Run Unit Tests
        run: ant test

  ollama-create-review:
    runs-on: self-hosted
    needs: build

    steps:

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Verify API Server
        run: |
          curl http://10.243.109.249:8000/docs

      - name: Generate Code
        run: |
          curl -X POST http://10.243.109.249:8000/create \
          -H "Authorization: Bearer ${{ secrets.LLM_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d '{
            "prompt": "Write a Python implementation of quick sort."
          }' > generated.json

      - name: Show Generated Code
        run: cat generated.json

      - name: Review Generated Code
        run: |
          CODE=$(cat generated.json)

          curl -X POST http://10.243.109.249:8000/review \
          -H "Authorization: Bearer ${{ secrets.LLM_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d "{\"code\":\"$CODE\"}" > review.json

      - name: Show Review
        run: cat review.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: ollama-results
          path: |
            generated.json
            review.json
```

---

# Part 11 — Add GitHub Secret

In GitHub:

```text
Repository
→ Settings
→ Secrets and Variables
→ Actions
→ New Repository Secret
```

Create:

```text
LLM_API_KEY
```

Value:

```text
your_secret_key
```

---

# Part 12 — Test Remote API

From another machine:

```bash
curl -X POST http://10.243.109.249:8000/review \
  -H "Authorization: Bearer your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"code":"print(\"hello\")"}'
```

---

# Part 13 — Optional Improvements

## Add Structured Prompts

Use prompts such as:

```text
You are a senior software engineer.

Review:
- bugs
- performance
- security
- readability
- edge cases
```

---

## Add Rate Limiting

Recommended package:

```bash
pip install slowapi
```

---

## Add Logging

Log:

- requests
- prompts
- execution time
- errors

Useful for:

- debugging
- research
- analytics

---

## Use Different Models per Task

Recommended setup:

| Task | Model |
|---|---|
| Code Generation | phi3.5 |
| Code Review | mistral |
| Lightweight Review | phi3 |

---

# Part 14 — How the Full System Works

Execution flow:

1. Developer pushes code
2. GitHub Actions workflow starts
3. Cloud runner performs build/tests
4. Self-hosted runner receives AI job
5. FastAPI server receives API request
6. FastAPI communicates with Ollama
7. Ollama executes local model
8. Results returned to GitHub Actions
9. Artifacts uploaded to GitHub

---

# Final Architecture

```text
Developer Push
      ↓
GitHub Actions
      ↓
-------------------------------
| GitHub Cloud Runner         |
| Build / Tests / Checkstyle  |
-------------------------------
      ↓
-------------------------------
| Self-Hosted Runner          |
| FastAPI + Ollama            |
-------------------------------
      ↓
Local LLM Inference
      ↓
Results + Artifacts
```
