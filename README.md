# Hybrid GitHub Actions with Self-Hosted Ollama API Server

## Overview

This project demonstrates how to integrate a locally hosted Ollama LLM server with GitHub Actions using:

- A self-hosted GitHub Actions runner
- A custom FastAPI API wrapper (`server.py`)
- Ollama running locally on a Linux server
- GitHub Actions sending prompts to the LLM API

This architecture allows:

- AI-powered code review
- AI-generated code
- Local/private inference
- No dependency on external paid APIs
- Research experimentation with local LLMs

---

# Final Architecture

```text
GitHub Push / Pull Request
            ↓
GitHub Actions Workflow
            ↓
----------------------------------
| GitHub Hosted Runner           |
| or Self-hosted Runner          |
----------------------------------
            ↓
Custom FastAPI API (server.py)
            ↓
Ollama Local API
            ↓
phi3.5 / mistral / codellama
            ↓
LLM Response
            ↓
GitHub Actions Logs / PR Comments
```

---

# Step 0 — Create Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

# Step 1 — Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify:

```bash
ollama --version
```

---

# Step 2 — Start Ollama

```bash
ollama serve
```

---

# Step 3 — Download Models

```bash
ollama pull phi3.5
ollama pull mistral
ollama pull codellama
```

List models:

```bash
ollama list
```

---

# Step 4 — Test Ollama

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "phi3.5",
  "prompt": "hello",
  "stream": false
}'
```

---

# Step 5 — Install Python Dependencies

```bash
pip install fastapi uvicorn requests
```

Verify:

```bash
python -m uvicorn --version
```

---

# Step 6 — Create Project Folder

```bash
mkdir -p ~/workspace/exposed_ollama
cd ~/workspace/exposed_ollama
```

---

# Step 7 — Create `server.py`

```python
from fastapi import FastAPI, Request, HTTPException
import requests
import re

app = FastAPI()

API_KEY = "your_secret_key"

OLLAMA_URL = "http://localhost:11434/api/generate"

CREATE_MODEL = "phi3.5"
REVIEW_MODEL = "mistral"


def call_llm(prompt, model):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()

    return response.json()["response"]


def extract_code(text):
    match = re.search(r"```(?:python)?\n(.*?)```", text, re.DOTALL)

    if match:
        return match.group(1).strip()

    return text.strip()


@app.post("/create")
async def create_code(request: Request):

    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()

    prompt = data.get("prompt")

    full_prompt = f"""
You are an expert software engineer.

Generate code only.

Do not explain anything.

Task:
{prompt}
"""

    result = call_llm(full_prompt, CREATE_MODEL)

    return {
        "code": extract_code(result)
    }


@app.post("/review")
async def review_code(request: Request):

    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = await request.json()

    code = data.get("code")

    full_prompt = f"""
You are a senior software engineer.

Review this code carefully.

Focus on:
- bugs
- edge cases
- readability
- performance
- security
- maintainability

Code:
{code}
"""

    result = call_llm(full_prompt, REVIEW_MODEL)

    return {
        "review": result
    }
```

---

# Step 8 — Test API Server

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

Test:

```bash
curl -X POST http://localhost:8000/create \
  -H "Authorization: Bearer your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write Python quicksort"
  }'
```

---

# Step 9 — Create systemd Service

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
User=your_username
WorkingDirectory=/home/your_username/workspace/exposed_ollama
ExecStart=/home/your_username/workspace/exposed_ollama/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

# Step 10 — Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable llm-api
sudo systemctl start llm-api
sudo systemctl status llm-api
```

---

# Step 11 — Open Firewall

```bash
sudo ufw allow 8000
```

---

# Step 12 — Create GitHub Self-Hosted Runner

Go to:

```text
Settings → Actions → Runners → New self-hosted runner
```

Install runner:

```bash
mkdir actions-runner && cd actions-runner

curl -o actions-runner.tar.gz -L \
https://github.com/actions/runner/releases/download/v2.333.1/actions-runner-linux-x64-2.333.1.tar.gz

tar xzf actions-runner.tar.gz
```

Configure:

```bash
./config.sh --url https://github.com/YOUR_REPO --token YOUR_TOKEN
```

Run:

```bash
./run.sh
```

Install as service:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

---

# Step 13 — GitHub Workflow Example

Create:

```text
.github/workflows/llm-review.yml
```

```yaml
name: LLM Code Review

on:
  pull_request:

jobs:

  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build Step
        run: echo "Building project..."

  llm-review:
    runs-on: self-hosted
    needs: build

    steps:
      - uses: actions/checkout@v4

      - name: Verify API Health
        run: curl http://10.243.109.249:8000/docs

      - name: Generate Code
        run: |
          curl -X POST http://10.243.109.249:8000/create \
          -H "Authorization: Bearer ${{ secrets.LLM_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d '{
            "prompt": "Write Python quicksort"
          }' > generated.json

      - name: Show Generated Code
        run: cat generated.json

      - name: Review Code
        run: |
          CODE=$(cat generated.json)

          curl -X POST http://10.243.109.249:8000/review \
          -H "Authorization: Bearer ${{ secrets.LLM_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d "{
            \"code\": \"$CODE\"
          }" > review.json

      - name: Show Review
        run: cat review.json
```

---

# Step 14 — Add GitHub Secret

Go to:

```text
Settings → Secrets and Variables → Actions
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

# Useful Commands

Restart Ollama:

```bash
sudo systemctl restart ollama
```

Restart API:

```bash
sudo systemctl restart llm-api
```

View logs:

```bash
sudo journalctl -u llm-api -f
```

---

# Recommended Improvements

- Add HTTPS using Nginx + Let's Encrypt
- Add rate limiting using slowapi
- Add logging
- Add automatic PR comments
- Use separate models:
  - create → phi3.5
  - review → mistral
  - advanced review → codellama
