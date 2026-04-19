# helloworld-ant
# Hybrid GitHub Actions with Self-Hosted Runner (Ollama Integration)

## Overview

This project implements a **hybrid CI/CD pipeline** using GitHub Actions where:

- **Job 1 (Cloud)** runs on GitHub-hosted runners for:
  - Build
  - Unit tests (JUnit)
  - Code quality checks

- **Job 2 (Local Server)** runs on a self-hosted runner on an ENMU server for:
  - AI inference using Ollama
  - Local model execution
  - Experimentation and analysis tasks

---

## Architecture

```
GitHub Push
    ↓
GitHub Actions Trigger
    ↓
-----------------------------
| Job 1 → GitHub VM        |
| Job 2 → ENMU Server      |
-----------------------------
    ↓
Self-hosted runner executes Ollama locally
    ↓
Results returned to GitHub
```

---

## Part 1 — Server Setup

### 1. SSH into server

```bash
ssh your_user@your_server
```

---

### 2. Install dependencies

```bash
sudo apt update
sudo apt install -y curl git
```

---

### 3. Verify Ollama installation

```bash
curl http://localhost:11434/api/tags
```

You should see installed models.

---

## Part 2 — Create GitHub Runner

### 4. Navigate to GitHub

Repository:

```
Settings → Actions → Runners → New self-hosted runner
```

Choose:
- Linux
- x64

---

### 5. Download runner (on server)

```bash
mkdir actions-runner && cd actions-runner

curl -o actions-runner.tar.gz -L https://github.com/actions/runner/releases/download/v2.333.1/actions-runner-linux-x64-2.333.1.tar.gz

tar xzf actions-runner.tar.gz
```

---

### 6. Configure runner

```bash
./config.sh --url https://github.com/YOUR_REPO --token YOUR_TOKEN
```

When prompted:

- Runner group → press ENTER (Default)
- Runner name → e.g. enmu-cs-server
- Labels → optional (e.g. campus, ollama)
- Work folder → press ENTER

---

### 7. Start runner

```bash
./run.sh
```

You should see:

```
Listening for Jobs
```

---

### 8. Install as service (recommended)

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

Check status:

```bash
sudo ./svc.sh status
```

---

## Part 3 — GitHub Workflow Setup

Create file:

```
.github/workflows/ci.yml
```

---

### 9. Hybrid CI Pipeline

```yaml
name: Hybrid CI

on:
  push:
    branches: [ main ]

jobs:

  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: 17

      - name: Install Ant
        run: sudo apt-get update && sudo apt-get install -y ant

      - name: Run tests
        run: ant test


  ollama:
    runs-on: self-hosted
    needs: build

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Check Ollama models
        run: curl http://localhost:11434/api/tags

      - name: Run Ollama prompt
        run: |
          curl http://localhost:11434/api/generate \
          -d '{
            "model": "mistral",
            "prompt": "Explain continuous integration in simple terms"
          }' > ollama_output.json

      - name: Upload result
        uses: actions/upload-artifact@v4
        with:
          name: ollama-output
          path: ollama_output.json
```

---

## Part 4 — Push and Test

```bash
git add .
git commit -m "Add hybrid CI pipeline with Ollama"
git push
```

---

## Part 5 — How It Works

### Execution Flow

1. Developer pushes code
2. GitHub triggers workflow
3. Job 1 runs on GitHub VM
4. Job 2 is queued for self-hosted runner
5. Runner on ENMU server pulls job
6. Executes locally with Ollama
7. Sends results back to GitHub

---

## Important Notes

### Security
- Only trusted workflows should run on self-hosted runner
- Avoid running untrusted pull requests

Recommended trigger:

```yaml
on:
  push:
    branches: [ main ]
```

---

## Result

You now have a hybrid system where:

- GitHub handles CI orchestration
- Cloud VM handles builds and testing
- ENMU server handles AI inference (Ollama)
- Results are stored in GitHub artifacts

---

## Final Architecture

```
GitHub Actions (Orchestrator)
        ↓
Cloud Runner → Build/Test
        ↓
Self-hosted Runner (ENMU Server)
        ↓
Ollama AI Execution
        ↓
Artifacts → GitHub
```

