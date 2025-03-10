from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Load persistent memory
with open("memory.txt", "r") as file:
    memory_content = file.read()

# Store chat history
chat_history = []

def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    return response.json().get("data", []) if response.status_code == 200 else []

def format_properties(properties):
    formatted = ""
    for prop in properties[:5]:  # limit the number to avoid long replies
        name = prop.get('property_title', 'Unnamed')
        locality = prop.get('project', {}).get('locality', 'Unknown location')
        price = prop.get('price')
        price_display = f"₹{price:,.0f}" if price else "Price not disclosed"
        bhk = prop.get('bedrooms', 'N/A')
        status = prop.get('property_status', 'Unknown status')
        url = prop.get('property_url', '#')
        formatted = (
            f"**{name}**\n"
            f"- 📍 Location: {locality}\n"
            f"- 💰 Price: {price_display}\n"
            f"- 🛏️: {bhk} BHK\n"
            f"- 🏷️ Status: {status}\n"
            f"- 🔗 [View details]({url})\n\n"
        )
    return formatted_props if formatted_props else "Currently, no properties are available."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    chat_history.append({"role": "user", "content": user_message})

    # Clearly instruct AI to collect required info first
    clear_instruction = """
    ALWAYS ensure you have these three details from user explicitly before recommending properties:
    1. Desired Location
    2. Budget
    3. Apartment type (2BHK or 3BHK)

    If missing any detail, politely ask.

    Keep your replies concise (under 4 sentences) unless showing property details.
    Use emojis (📍 for location, 💸 for budget, 🛏️ for bedrooms). Provide markdown clickable links.
    """

    full_system_prompt = f"""
    {system_prompts.get(personality, 'formal')}

    MEMORY:
    {memory_content}

    Available properties:
    {fetch_properties()}

    {recent_conversation}
    """

    messages = [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    reply = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
