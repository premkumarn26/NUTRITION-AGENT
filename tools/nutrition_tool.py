import requests
from ibm_watsonx_orchestrate.agent_builder.tools import tool

WX_URL = "https://eu-de.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
MODEL_ID = "ibm/granite-4-h-small"
PROJECT_ID = "4a35f5bc-7a61-40bd-b561-23aca2097499"
API_KEY = "6MKpl_8g8jVuvWiO8cebYWX0tFhqFjqpybZ5trhKPLgj"


def _get_iam_token() -> str:
    """Exchange IBM API key for a short-lived IAM bearer token."""
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


def _call_granite(prompt: str, max_tokens: int = 600) -> str:
    """Send a prompt to IBM Granite and return the generated text."""
    token = _get_iam_token()
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
    if results:
        return results[0].get("generated_text", "").strip()
    return "No response generated."


@tool
def generate_nutrition_plan(
    age: int,
    gender: str,
    weight_kg: float,
    height_cm: float,
    goal: str,
    dietary_preference: str,
    activity_level: str,
    health_conditions: str = "None",
) -> str:
    """
    Generate a personalised daily nutrition plan for a client.

    Args:
        age: Client age in years.
        gender: Client gender (Male / Female / Other).
        weight_kg: Current body weight in kilograms.
        height_cm: Height in centimetres.
        goal: Primary goal — e.g. 'Weight Loss', 'Muscle Gain', 'Maintenance', 'Improve Energy'.
        dietary_preference: e.g. 'Omnivore', 'Vegetarian', 'Vegan', 'Keto', 'Gluten-Free'.
        activity_level: e.g. 'Sedentary', 'Lightly Active', 'Moderately Active', 'Very Active'.
        health_conditions: Any relevant health conditions or allergies (default: None).

    Returns:
        A detailed nutrition plan as a formatted string.
    """
    prompt = (
        f"You are a certified nutritionist. Create a detailed, practical daily nutrition plan "
        f"for the following client.\n\n"
        f"Client Profile:\n"
        f"- Age: {age} years\n"
        f"- Gender: {gender}\n"
        f"- Weight: {weight_kg} kg\n"
        f"- Height: {height_cm} cm\n"
        f"- Goal: {goal}\n"
        f"- Dietary Preference: {dietary_preference}\n"
        f"- Activity Level: {activity_level}\n"
        f"- Health Conditions / Allergies: {health_conditions}\n\n"
        f"Please provide:\n"
        f"1. Daily calorie target and macronutrient breakdown (protein, carbs, fats)\n"
        f"2. A sample meal plan (Breakfast, Mid-Morning Snack, Lunch, Afternoon Snack, Dinner)\n"
        f"3. Hydration recommendation\n"
        f"4. 3-5 key nutrition tips tailored to the client's goal\n"
        f"5. Foods to avoid\n\n"
        f"Format the response clearly with section headings."
    )
    return _call_granite(prompt, max_tokens=800)


@tool
def get_food_nutrition_info(food_item: str, serving_size: str = "100g") -> str:
    """
    Retrieve nutritional information and health benefits for a specific food item.

    Args:
        food_item: Name of the food (e.g. 'quinoa', 'chicken breast', 'avocado').
        serving_size: Serving size to base the info on (default: '100g').

    Returns:
        Nutritional breakdown and health benefits as a formatted string.
    """
    prompt = (
        f"As a nutrition expert, provide a detailed nutritional profile for '{food_item}' "
        f"per {serving_size} serving. Include:\n"
        f"1. Calories\n"
        f"2. Macronutrients (protein, carbohydrates, fats, fibre)\n"
        f"3. Key vitamins and minerals\n"
        f"4. Top 3 health benefits\n"
        f"5. Best ways to include it in a diet\n"
        f"Format with clear headings."
    )
    return _call_granite(prompt, max_tokens=500)


@tool
def calculate_bmi_and_advice(weight_kg: float, height_cm: float) -> str:
    """
    Calculate BMI for a client and provide health advice based on the result.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimetres.

    Returns:
        BMI value, category, and tailored health advice.
    """
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    prompt = (
        f"A person has a BMI of {bmi} (weight: {weight_kg} kg, height: {height_cm} cm). "
        f"As a health expert:\n"
        f"1. State the BMI value and its category (Underweight / Normal / Overweight / Obese)\n"
        f"2. Explain what this means for their health\n"
        f"3. Provide 3 actionable nutrition recommendations to improve or maintain their health\n"
        f"Keep the response encouraging and practical."
    )
    result = _call_granite(prompt, max_tokens=400)
    return f"**Calculated BMI: {bmi}**\n\n{result}"
