# Nyaaya.ai — Welfare Benefits, Simplified

**AI-powered Indian government welfare eligibility engine** that helps citizens discover, qualify for, and apply to welfare schemes through a natural Hinglish conversation.

> Built for the **AWS AI For Bharat Hackathon** — Prototype Phase

---

## The Problem

**350M+ eligible Indians don't claim welfare benefits** because the process is confusing, multilingual, and bureaucratic. Forms are in English, rules are scattered across websites, and there's no one to guide them through.

## Our Solution

Nyaaya.ai is an end-to-end welfare eligibility platform that:

1. **Interviews** users in natural Hinglish (Hindi + English) via an empathetic AI assistant
2. **Extracts** structured eligibility data from conversational input
3. **Evaluates** against 6 welfare schemes using a deterministic rule engine
4. **Computes a Nyaaya Score** (0-100) — a novel "welfare accessibility index"
5. **Generates an optimised application strategy** with week-by-week timelines
6. **Creates personalised peer stories** so users learn from real-world experiences

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  React SPA  │────▶│  FastAPI + Lambda │────▶│  Amazon Bedrock     │
│  (Vite)     │     │  (Mangum)        │     │  (Claude Sonnet 4.5)│
└─────────────┘     └──────┬───────────┘     └─────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │ DynamoDB  │ │ Amazon   │ │ Amazon       │
        │ Sessions  │ │Translate │ │ Comprehend   │
        └──────────┘ └──────────┘ └──────────────┘
```

### AWS Services Used

| Service | Purpose |
|---------|---------|
| **Amazon Bedrock** (Claude Sonnet 4.5) | Hinglish interview, data extraction, story generation |
| **DynamoDB** | Session persistence with TTL auto-expiry |
| **Lambda** (via Mangum) | Serverless API hosting |
| **API Gateway** | REST endpoint routing |
| **Amazon Translate** | Real-time Hindi/English/Marathi translation |
| **Amazon Comprehend** | Language detection |
| **S3 + CloudFront** | Frontend static hosting |

---

## Welfare Schemes Covered (6)

| Scheme | Benefit | Target |
|--------|---------|--------|
| Widow Pension (Maharashtra) | ₹600/month | Widows, income <₹15K |
| Disability Allowance | ₹500/month | ≥40% disability, income <₹10K |
| NREGA Employment Guarantee | ₹20,000/year | Rural, 18-65, income <₹20K |
| PM-KISAN Samman Nidhi | ₹500/month | Farmers, rural, income <₹2L |
| Indira Gandhi Old Age Pension | ₹500/month | Age ≥60, BPL |
| PM Ujjwala Yojana (Free LPG) | ₹1,600 one-time | Women, BPL |

---

## Innovation Highlights

### Nyaaya Score (0-100)
A composite "welfare accessibility index" that quantifies how well-served a citizen is:
- **Coverage** (40%): % of schemes qualified for
- **Benefit** (30%): annual benefit vs ₹72K baseline income
- **Speed** (15%): inverse of average processing time
- **Confidence** (15%): average match confidence

Grades: A (80+), B (60+), C (40+), D (20+), F (<20)

### Bedrock-Powered Peer Stories
Instead of static FAQs, Nyaaya generates **personalised peer success stories** based on the user's state, district, and eligible schemes — complete with real-world blockers and practical tips.

### Hinglish-Native Interview
The AI naturally handles code-mixing (Hindi + English) and extracts structured data without forms. Voice input supported via Web Speech API.

### 3-Layer Validation Pipeline
1. **Pydantic** — type, range, cross-field validation
2. **Rule engine** — deterministic per-scheme eligibility (pure functions, zero side effects)
3. **Strategy optimizer** — ranked application timeline with phase-based scheduling

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS account with Bedrock access (Claude Sonnet 4.5)

### Backend

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs at http://localhost:8000/docs
# Uses mock DynamoDB locally — no AWS needed for basic testing
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Environment Variables

```bash
# Backend
AWS_REGION=ap-south-1
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250514
DYNAMODB_TABLE_NAME=nyaaya_interviews
USE_REAL_DYNAMODB=true  # only when using real AWS

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

---

## AWS Setup Guide

### 1. Enable Bedrock Model Access

Go to **Amazon Bedrock → Model access → Manage model access** in `ap-south-1`.
Request access to **Anthropic Claude Sonnet 4.5**. Approval is usually instant.

```bash
aws bedrock list-foundation-models --region ap-south-1 \
  --query "modelSummaries[?modelId=='anthropic.claude-sonnet-4-5-20250514'].modelId"
```

### 2. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name nyaaya_interviews \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1

aws dynamodb update-time-to-live \
  --table-name nyaaya_interviews \
  --time-to-live-specification "Enabled=true, AttributeName=ttl" \
  --region ap-south-1
```

### 3. Create IAM Role for Lambda

```bash
aws iam create-role \
  --role-name nyaaya-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy --role-name nyaaya-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam put-role-policy --role-name nyaaya-lambda-role \
  --policy-name nyaaya-services \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["bedrock:InvokeModel"],
        "Resource": "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-sonnet-4-5-20250514"
      },
      {
        "Effect": "Allow",
        "Action": ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem"],
        "Resource": "arn:aws:dynamodb:ap-south-1:*:table/nyaaya_interviews"
      },
      {
        "Effect": "Allow",
        "Action": ["translate:TranslateText", "comprehend:DetectDominantLanguage"],
        "Resource": "*"
      }
    ]
  }'
```

### 4. Deploy Lambda

```bash
pip install -r requirements.txt -t package/
cp *.py package/
cd package && zip -r ../nyaaya-lambda.zip . && cd ..

aws lambda create-function \
  --function-name nyaaya-api \
  --runtime python3.11 \
  --handler main.handler \
  --role arn:aws:iam::<ACCOUNT_ID>:role/nyaaya-lambda-role \
  --zip-file fileb://nyaaya-lambda.zip \
  --timeout 30 \
  --memory-size 512 \
  --environment Variables="{AWS_REGION=ap-south-1,DYNAMODB_TABLE_NAME=nyaaya_interviews,USE_REAL_DYNAMODB=true}" \
  --region ap-south-1
```

### 5. API Gateway

Create an **HTTP API** in API Gateway with Lambda integration.
Enable CORS (all origins for prototype). Note the invoke URL.

### 6. Deploy Frontend

```bash
cd frontend
VITE_API_URL=https://<api-gateway-url> npm run build
aws s3 mb s3://nyaaya-frontend --region ap-south-1
aws s3 sync dist/ s3://nyaaya-frontend --delete
```

Create a CloudFront distribution pointing to the S3 bucket.
Add error response: 404 → `/index.html` (SPA routing).

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/interview` | Multi-turn Hinglish interview (Bedrock) |
| `POST` | `/evaluate` | Evaluate eligibility + strategy + Nyaaya Score |
| `POST` | `/translate` | Translate text (Amazon Translate) |
| `POST` | `/stories` | Generate personalised peer stories (Bedrock) |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## Project Structure

```
├── main.py               # FastAPI app + Lambda handler (6 endpoints)
├── bedrock_client.py     # Amazon Bedrock interview + story generation
├── rule_engine.py        # Deterministic eligibility rules (6 schemes)
├── optimizer.py          # Strategy optimizer + Nyaaya Score computation
├── models.py             # Pydantic v2 schemas
├── config.py             # AWS config + constants + enums
├── dynamodb_utils.py     # DynamoDB session persistence (mock + real)
├── translate_client.py   # Amazon Translate + Comprehend integration
├── requirements.txt
├── tests/
│   ├── test_rule_engine.py
│   ├── test_bedrock_integration.py
│   └── test_api_endpoints.py
└── frontend/
    ├── src/
    │   ├── pages/        # Welcome, Interview, Results, Strategy, Stories
    │   ├── components/   # NyaayaScore, ChatBubble, VoiceButton, LanguageToggle
    │   └── api/client.js # API client
    ├── index.html
    └── package.json
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

Built with care for Bharat.
