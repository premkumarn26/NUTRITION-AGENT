"""
NutriCoach Backend Server
Bridges the frontend HTML to IBM Granite via watsonx.ai.
Run: python backend/app.py
"""

import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from the frontend served from any origin

# ── CONFIG ────────────────────────────────────────────────────
API_KEY    = os.getenv("IBM_API_KEY",    "6MKpl_8g8jVuvWiO8cebYWX0tFhqFjqpybZ5trhKPLgj")
PROJECT_ID = os.getenv("IBM_PROJECT_ID", "4a35f5bc-7a61-40bd-b561-23aca2097499")
WX_URL     = "https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
MODEL_ID   = "ibm/granite-4-h-small"

# ── IAM TOKEN HELPER ──────────────────────────────────────────
def get_iam_token() -> str:
    resp = requests.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def call_granite(prompt: str, max_tokens: int = 700) -> str:
    token = get_iam_token()
    payload = {
        "model_id": MODEL_ID,
        "project_id": PROJECT_ID,
        "input": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "repetition_penalty": 1.1,
        },
    }
    resp = requests.post(
        WX_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0].get("generated_text", "").strip() if results else "No response generated."


# ── ROUTES ────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": "nutrition_agent"})


@app.route("/chat", methods=["POST"])
def chat():
    """
    Accepts: { "message": "...", "thread_id": "..." (optional) }
    Returns: { "response": "...", "thread_id": "..." }
    """
    data = request.get_json(force=True)
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "message is required"}), 400

    system_context = (
        "You are NutriCoach, a friendly and knowledgeable AI nutrition assistant. "
        "You help users with personalised meal plans, food nutrition facts, BMI assessments, "
        "and evidence-based nutrition advice. "
        "Always respond with clear formatting: use section headings (##), bullet points, and bold text. "
        "Keep responses practical, encouraging, and medically responsible — "
        "always recommend consulting a doctor for medical concerns."
    )
    prompt = f"[INST] {system_context}\n\nUser: {user_message} [/INST]"

    try:
        answer = call_granite(prompt)
        return jsonify({"response": answer, "thread_id": data.get("thread_id", "session-1")})
    except requests.HTTPError as e:
        return jsonify({"error": f"Granite API error: {e}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/nutrition-plan", methods=["POST"])
def nutrition_plan():
    """
    Accepts: { age, gender, weight_kg, height_cm, goal, dietary_preference,
               activity_level, health_conditions }
    """
    d = request.get_json(force=True)
    required = ["age", "weight_kg", "height_cm", "goal", "dietary_preference", "activity_level"]
    missing  = [k for k in required if not d.get(k)]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    prompt = (
        f"[INST] You are a certified nutritionist. Create a detailed, practical daily nutrition plan "
        f"for the following client.\n\n"
        f"Client Profile:\n"
        f"- Age: {d['age']} years\n"
        f"- Gender: {d.get('gender', 'Not specified')}\n"
        f"- Weight: {d['weight_kg']} kg\n"
        f"- Height: {d['height_cm']} cm\n"
        f"- Goal: {d['goal']}\n"
        f"- Dietary Preference: {d['dietary_preference']}\n"
        f"- Activity Level: {d['activity_level']}\n"
        f"- Health Conditions / Allergies: {d.get('health_conditions', 'None')}\n\n"
        f"Provide:\n"
        f"1. Daily calorie target and macronutrient breakdown\n"
        f"2. Sample meal plan (Breakfast, Snack, Lunch, Snack, Dinner)\n"
        f"3. Hydration recommendation\n"
        f"4. 3-5 key nutrition tips\n"
        f"5. Foods to avoid [/INST]"
    )
    try:
        return jsonify({"response": call_granite(prompt, 900)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/food-info", methods=["POST"])
def food_info():
    """Accepts: { "food_item": "quinoa", "serving_size": "100g" }"""
    d = request.get_json(force=True)
    food = d.get("food_item", "").strip()
    if not food:
        return jsonify({"error": "food_item is required"}), 400
    serving = d.get("serving_size", "100g")

    prompt = (
        f"[INST] As a nutrition expert, provide a detailed nutritional profile for '{food}' "
        f"per {serving} serving. Include: calories, macros, key vitamins & minerals, "
        f"top 3 health benefits, and best ways to include it in a diet. "
        f"Use clear headings and bullet points. [/INST]"
    )
    try:
        return jsonify({"response": call_granite(prompt, 500)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/bmi", methods=["POST"])
def bmi():
    """Accepts: { "weight_kg": 70, "height_cm": 175 }"""
    d = request.get_json(force=True)
    w = float(d.get("weight_kg", 0))
    h = float(d.get("height_cm", 0))
    if not w or not h:
        return jsonify({"error": "weight_kg and height_cm are required"}), 400

    bmi_val = round(w / ((h / 100) ** 2), 1)
    prompt  = (
        f"[INST] A person has a BMI of {bmi_val} (weight: {w} kg, height: {h} cm). "
        f"As a health expert: state the BMI category, explain what this means for health, "
        f"and provide 3 actionable nutrition recommendations. Be encouraging and practical. [/INST]"
    )
    try:
        result = call_granite(prompt, 400)
        return jsonify({"bmi": bmi_val, "response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── RUN ───────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"🥗 NutriCoach backend running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
