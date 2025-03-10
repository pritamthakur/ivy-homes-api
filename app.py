from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import os

app = Flask(__name__)
CORS(app)

# Load your OpenAI API key from Render's environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load memory content once
with open("memory.txt", "r") as file:
    memory = file.read().strip()

system_prompts = {
    "funny": "You're funny, humorous, playful, and outrageous. Use Indian context humor; say prices are over the roof!",
    "cranky": "You're cranky, irritated, sarcastic, and blunt. Use phrases like 'bhai khareedna hai toh batao'.",
    "formal": "You're formal, polite, professional, and helpful."
}

chat_history = []

def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    return response.json().get("data", []) if response.status_code == 200 else []

def find_relevant_properties(location, budget, bhk_type):
    properties = fetch_properties()
    filtered = []

    for prop in properties:
        prop_locality = prop.get('project', {}).get('locality', '').lower()
        prop_price = prop.get('price') or 0
        prop_bhk = prop.get('bedrooms')

        if location.lower() in prop_locality and (budget is None or prop_price <= budget) and (bhk_type is None or bhk_type == prop_bhk):
            filtered.append(prop)

    # If no exact matches, find closest location
    if not filtered and location:
        for prop in properties:
            if location.lower().split()[0] in prop.get('project', {}).get('locality', '').lower():
                filtered.append(prop)
                break  # Nearest match

    return filtered[:3]  # Limit to top 3 properties

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    chat_history.append({"role": "user", "content": user_message})

    conversation = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history[-6:]])

    full_system_prompt = (
        f"{system_prompts.get(personality, 'formal')}\n\n"
        f"Memory:\n{memory}\n\n"
        "ALWAYS clearly ask user for these details BEFORE suggesting properties:\n"
        "1. Desired Location?\n"
        "2. Budget?\n"
        "3. Type (2BHK/3BHK)?\n\n"
        "If user's requested location isn't available, suggest the nearest location clearly mentioning it.\n\n"
        "Once you clearly have the above 3 details, ONLY THEN suggest properties (max 3) with emojis, formatted neatly, and clickable links.\n\n"
        f"Recent conversation:\n{conversation}"
    )

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
