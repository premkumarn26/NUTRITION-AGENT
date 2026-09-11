# 🥗 NutriCoach — AI Nutrition Agent

A full-stack AI nutrition assistant powered by **IBM Granite** (`ibm/granite-4-h-small`) on watsonx.ai, deployed as a native agent on **IBM watsonx Orchestrate**.

---

## Architecture

```
┌─────────────────────┐     HTTP      ┌──────────────────────┐     IAM + REST    ┌──────────────────┐
│  frontend/index.html│ ──────────►  │  backend/app.py      │ ───────────────►  │  IBM watsonx.ai  │
│  (HTML/CSS/JS SPA)  │              │  (Flask REST server)  │                   │  Granite model   │
└─────────────────────┘              └──────────────────────┘                   └──────────────────┘
                                               │
                                       watsonx Orchestrate
                                       ┌──────────────────┐
                                       │  nutrition_agent  │
                                       │  + 3 Python tools │
                                       └──────────────────┘
```

---

## Project Structure

```
NUTRITION_AGENT/
├── frontend/
│   └── index.html          ← Single-page frontend (Chat, BMI, Tips)
├── backend/
│   └── app.py              ← Flask REST backend (bridges UI ↔ Granite)
├── tools/
│   └── nutrition_tool.py   ← watsonx Orchestrate Python tools (3 tools)
└── requirements.txt
```

---

## Tools (registered in watsonx Orchestrate)

| Tool | Description |
|------|-------------|
| `generate_nutrition_plan` | Builds a personalised daily meal plan from client profile |
| `get_food_nutrition_info` | Returns macros, vitamins, and benefits for any food item |
| `calculate_bmi_and_advice` | Calculates BMI and gives targeted nutrition advice |

---

## Agent (watsonx Orchestrate)

- **Name:** `nutrition_agent`
- **Model:** `ibm/granite-4-h-small`
- **Style:** ReAct (tool-use reasoning)
- **ID:** `c8cbfc29-f86e-4e41-b131-3883ac437629`

---

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the backend server
```bash
python backend/app.py
# → http://localhost:5000
```

### 3. Open the frontend
Open `frontend/index.html` in your browser.  
The frontend talks to `http://localhost:5000` by default.

---

## Environment Variables (optional)

| Variable | Default | Description |
|---|---|---|
| `IBM_API_KEY` | (hardcoded) | IBM Cloud API key |
| `IBM_PROJECT_ID` | (hardcoded) | watsonx.ai project ID |
| `PORT` | `5000` | Backend server port |

---

## Frontend Features

| Page | Description |
|------|-------------|
| **Chat** | Conversational nutrition coach with quick prompts and sidebar shortcuts |
| **BMI Tool** | Instant BMI calculation + AI health advice |
| **Nutrition Tips** | Curated evidence-based tips by goal (Weight Loss, Muscle Gain, etc.) |
