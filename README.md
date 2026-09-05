# TIMI STEMI Risk Score

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics
> **Reference Guidelines & Standards:** AHA/ACC Practice Guidelines & ESC Clinical Standards

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-23%20Passed-brightgreen.svg)

</div>

---

## 📖 What It Does

TIMI Risk Score for STEMI calculates 30-day mortality risk in ST-elevation myocardial infarction patients from clinical variables. The system provides:

- **Single-case evaluation** with clinical classification and recommendations
- **Batch CSV processing** for high-throughput analysis
- **REST API** via FastAPI for integration with clinical systems
- **Multi-agent consensus** with specialized workers for QC, safety, and protocol conformance

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/timi-stemi-risk-score.git
cd timi-stemi-risk-score

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 Usage

### 1. Single Case Evaluation

```bash
python timi_stemi.py single --v1 12.0 --v2 4.0 --v3 2.0
```

Output:
```json
{
  "tool": "timi-stemi-risk-score",
  "score": 14.0,
  "classification": "Moderate / Intermediate",
  "clinical_recommendation": "Close observation or secondary evaluation",
  "inputs_evaluated": 3
}
```

### 2. Batch CSV Processing

```bash
python timi_stemi.py batch -i input.csv -o results.csv
```

Input CSV format:
```csv
Patient_ID,v1,v2,v3
Pat_001,15.0,3.0,1.0
Pat_002,5.0,1.0,0.5
```

### 3. Enterprise Supervisor CLI

```bash
# Set audit key (required)
set AUDIT_SECRET_KEY=your-secure-min-16-char-key-here

# Run single audit task
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i input.csv -o results.csv

# Verify audit integrity
python cli.py verify-audit

# Start API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### 4. Python API

```python
from timi_stemi import calculate_metrics

result = calculate_metrics(v1=12.0, v2=4.0)
print(result["score"])           # 14.0
print(result["classification"]) # "Moderate / Intermediate"
```

---

## 📐 Classification Tiers

| Score Range | Classification | Recommendation |
|:------------|:---------------|:---------------|
| < 10.0 | Low / Standard | Standard monitoring or negative cutoff |
| 10.0 - 24.99 | Moderate / Intermediate | Close observation or secondary evaluation |
| >= 25.0 | High / Severe | Urgent clinical intervention |

---

## 🛡️ Security Architecture

### Zero-PHI Outbound Guard
Active pattern detection and blocking of:
- Medical Record Numbers (MRN)
- Social Security Numbers (SSN)
- Phone numbers and email addresses
- Patient names (e.g., "John Doe")
- Date of birth patterns

### HMAC-SHA256 Audit Trail
- **Requires** `AUDIT_SECRET_KEY` environment variable (minimum 16 characters)
- Cryptographic chaining of all audit entries
- Tamper-evident integrity verification
- No hardcoded secrets

### Path Traversal Protection
All file operations validate paths to prevent directory traversal attacks.

---

## 🧪 Testing

```bash
# Run full test suite (23 tests)
pytest -v

# Run with coverage
pytest --cov=agents --cov=timi_stemi --cov-report=html

# Run specific test file
pytest test_timi_stemi.py -v
pytest tests/test_timi_stemi_risk_score.py -v
pytest tests/test_enrichment.py -v
```

---

## 🐳 Docker Deployment

```bash
docker build -t timi-stemi-risk-score .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key timi-stemi-risk-score
```

---

## 📁 Project Structure

```
timi-stemi-risk-score/
├── agents/                  # Enterprise multi-agent system
│   ├── __init__.py          # Package initialization
│   ├── api.py               # FastAPI REST endpoints
│   ├── base.py              # Security guards, audit trail, PHI protection
│   ├── learning.py          # Bayesian calibration engine
│   ├── llm_factory.py       # LLM provider factory
│   ├── metrics.py           # Prometheus metrics collector
│   ├── models.py            # Pydantic data models
│   ├── streamer.py          # WebSocket telemetry
│   ├── supervisor.py        # Orchestrator coordinator
│   └── workers.py           # Specialized analysis workers
├── tests/                   # Test suite
│   ├── test_enrichment.py
│   └── test_timi_stemi_risk_score.py
├── test_timi_stemi.py       # Core module tests
├── timi_stemi.py            # Core TIMI STEMI calculation engine
├── cli.py                   # Enterprise CLI
├── enrichment.py            # Extended feature engines
├── simulator.py             # High-throughput stress testing
├── conftest.py              # Pytest configuration
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container definition
└── docker-compose.yml       # Multi-service orchestration
```

---

## 🔧 Dependencies

- Python 3.10+
- FastAPI >= 0.111.0
- Pydantic >= 2.5.0
- uvicorn >= 0.30.0
- pytest >= 8.0.0

---

## 📝 Environment Variables

| Variable | Required | Description |
|:---------|:---------|:------------|
| `AUDIT_SECRET_KEY` | Yes | HMAC-SHA256 key for audit trail (min 16 chars) |
