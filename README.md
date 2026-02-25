# Nyaaya.ai Backend — Eligibility Brain

AI-powered Indian government welfare eligibility platform. Users converse in Hinglish → Claude 3.5 Sonnet extracts structured facts → deterministic rule engine checks eligibility → strategy optimizer generates a week-by-week application plan.

## Architecture

```
User (Hinglish) → POST /interview → Bedrock Claude 3.5 Sonnet → DynamoDB session
                → POST /evaluate  → Rule Engine → Strategy Optimizer → JSON response
```

## Project Structure

```
Nyaaya/
├── main.py              # FastAPI app + Mangum Lambda handler
├── models.py            # Pydantic v2 schemas (UserProfile, InterviewState, …)
├── rule_engine.py       # SchemeValidator — 3 deterministic rules + ME resolver
├── bedrock_client.py    # Claude 3.5 Sonnet interview orchestration
├── optimizer.py         # Strategy ranking + phase assignment
├── dynamodb_utils.py    # DynamoDB mock + real boto3 client
├── config.py            # AWS config, constants, shared enums
├── requirements.txt
└── tests/
    ├── conftest.py
    ├── test_rule_engine.py
    ├── test_bedrock_integration.py
    └── test_api_endpoints.py
```

## Supported Schemes

| ID | Name | States | Monthly Benefit |
|----|------|--------|-----------------|
| `widow_pension_mh` | Widow Pension | Maharashtra | ₹600 |
| `disability_allowance` | Disability Allowance | All | ₹500 |
| `nrega` | NREGA Employment | MH / RJ / UP | ₹20,000/year |

## Local Development

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the API
```bash
uvicorn main:app --reload --port 8000
```
- Swagger UI: http://localhost:8000/docs
- By default, the **MockDynamoDBClient** is used (no AWS needed locally).

### 3. Run tests
```bash
# From project root
pytest tests/ -v
```

### 4. Point to real DynamoDB
```bash
export USE_REAL_DYNAMODB=1
export AWS_REGION=ap-south-1
export DYNAMODB_TABLE_NAME=nyaaya_interviews
uvicorn main:app --reload
```

## API Endpoints

### `POST /interview`
Multi-turn Hinglish interview powered by Bedrock.

**Request**
```json
{ "user_input": "Mera husband 5 saal pehle pass ho gaya", "session_id": "sess_abc123" }
```

**Response (200)**
```json
{
  "status": "success",
  "turn": 1,
  "next_question": "Bahut dukh ki baat hai. Aapki umar kya hai?",
  "extracted_so_far": { "marital_status": "widow", "life_event": "widow" },
  "interview_complete": false
}
```

---

### `POST /evaluate`
Direct eligibility evaluation from a fully-formed profile.

**Request**: `UserProfile` JSON  
**Response (200)**
```json
{
  "status": "success",
  "eligible_schemes": [ { "scheme_id": "widow_pension_mh", "eligible": true, … } ],
  "strategy": [ { "rank": 1, "apply_week": 1, … } ],
  "summary": { "total_monthly_benefit": 600, "first_year_total": 7200, … }
}
```

## DynamoDB Table Schema

Table name: `nyaaya_interviews`  
PK: `session_id` (String) — no SK.  
TTL attribute: `ttl` (Number, epoch seconds, 24-hour expiry).

Create with AWS CLI:
```bash
aws dynamodb create-table \
  --table-name nyaaya_interviews \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-south-1
```

Enable TTL:
```bash
aws dynamodb update-time-to-live \
  --table-name nyaaya_interviews \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region ap-south-1
```

## Lambda Deployment

`handler` in `main.py` is the Mangum-wrapped Lambda entry point.

```
Handler: main.handler
Runtime: python3.12
Timeout: 30s
Memory:  512MB
Environment variables:
  AWS_REGION=ap-south-1
  BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022
  DYNAMODB_TABLE_NAME=nyaaya_interviews
  USE_REAL_DYNAMODB=1
```

Required IAM permissions:
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel",
    "dynamodb:PutItem",
    "dynamodb:GetItem"
  ],
  "Resource": "*"
}
```

## Validation Layers

1. **Pydantic (Layer 1)** — type, range, required fields → HTTP 422  
2. **Business logic (Layer 2)** — ELDERLY/age consistency, disability cert pair → HTTP 422  
3. **Rule engine (Layer 3)** — deterministic eligibility, always returns True/False  

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | `ap-south-1` | AWS region |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022` | Bedrock model |
| `DYNAMODB_TABLE_NAME` | `nyaaya_interviews` | DynamoDB table |
| `USE_REAL_DYNAMODB` | *(unset)* | Set to `1` to use real DynamoDB |
