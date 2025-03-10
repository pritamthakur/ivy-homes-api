from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import os

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

with open("memory.txt", "r") as file:
    memory_content = file.read()

chat_history = []

def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    return response.json().get("data", []) if response.status_code == 200 else []

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    system_prompts = {
        "funny": "You're funny, humorous, playful, outrageous, and use Indian humor about high prices.",
        "cranky": "You're cranky, sarcastic, blunt, frequently saying 'bhai khareedna hai toh batao'.",
        "formal": "You're polite, professional, helpful, and concise."
    }

    instruction = (
        "Before suggesting properties, ALWAYS explicitly confirm the user's:\n"
        "1. Desired Location\n"
        "2. Budget\n"
        "3. Apartment type (2BHK or 3BHK)\n\n"
        "If any detail is missing, ask clearly for it. Do NOT show property listings until these are confirmed.\n"
        "Keep replies short (max 4-5 sentences). Use emojis.\n"
        "Only show property listings AFTER the user confirms all 3 details explicitly."
    )

    # Add the new user message to chat history
    chat_history.append({"role": "user", "content": user_message})

    # Check if the user provided all required details explicitly in the history
    user_details_confirmed = any(
        all(keyword in msg["content"].lower() for keyword in ["location", "budget", "bhk"])
        for msg in chat_history if msg["role"] == "assistant"
    )

    messages = [
        {"role": "system", "content": f"{system_prompts.get(personality)}\n\n{instruction}\n\nMemory Info:\n{memory_content}"}
    ] + chat_history

    # Only add property data if all user details are confirmed
    if user_details_confirmed:
        properties = fetch_properties()
        formatted_properties = "Available properties:\n"
        for prop in properties[:5]:
            name = prop.get('property_title', 'Unnamed')
            locality = prop.get('project', {}).get('locality', 'Unknown')
            price = prop.get('price', 'Price not disclosed')
            bhk = prop.get('bedrooms', 'N/A')
            url = prop.get('property_url', '#')
            formatted_properties += (
                f"- 🏡 {name}, 📍 {locality}, 🛏️ {bhk} BHK, 💰 ₹{price:,.0f}, [🔗 details]({url})\n"
            )
        messages.append({"role": "system", "content": formatted_properties})

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Add assistant's reply to the history
    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
