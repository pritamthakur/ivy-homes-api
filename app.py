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

# Global chat history (per deployment - basic implementation)
chat_history = []

def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    return response.json().get("data", []) if response.status_code == 200 else []

def format_properties(filtered_props):
    formatted_props = ""
    for prop in filtered_props[:5]:
        name = prop.get('property_title', 'Unnamed')
        locality = prop.get('project', {}).get('locality', 'Unknown')
        price = prop.get('price', None)
        formatted_price = f"₹{price:,.0f}" if price else "Price not disclosed"
        bhk = prop.get('bedrooms', 'N/A')
        status = prop.get('property_status', 'Unknown')
        url = prop.get('property_url', '#')

        formatted_props += (
            f"🏡 **{name}**\n"
            f"- 📍 {locality}\n"
            f"- 🛏️ {bhk} BHK\n"
            f"- 💰 {formatted_price}\n"
            f"- 🚦 {status}\n"
            f"- 🔗 [View details]({url})\n\n"
        )
    return formatted_props if formatted_props else "No properties match your criteria."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    properties = fetch_properties()

    system_prompts = {
        "funny": "You're funny, humorous, playful, and outrageous. Use Indian context humor; joke about high prices.",
        "cranky": "You're cranky, sarcastic, and blunt. Frequently say 'bhai khareedna hai toh batao'.",
        "formal": "You're polite, professional, and concise."
    }

    # Clear instructions for the AI
    clear_instruction = """
    Before recommending properties, explicitly confirm the user's:
    1. Desired Location
    2. Budget
    3. Apartment type (2BHK or 3BHK).

    If any detail is missing, ask for it clearly. Always keep replies concise (4-5 sentences maximum) unless providing a property list. Use emojis (📍 for location, 💰 for budget, 🛏️ for bedrooms) and provide markdown clickable links.
    """

    # Maintain chat history for context
    chat_history.append({"role": "user", "content": user_message})

    # Prepare recent conversation history (limit last 8 interactions to control tokens)
    recent_history = chat_history[-8:]

    messages = [
        {"role": "system", "content": f"{system_prompts.get(personality, 'formal')}\n\n{clear_instruction}\n\nMemory Info:\n{memory_content}\n"},
        *recent_history,
        {"role": "system", "content": f"Properties Data:\n{properties}"}
    ]

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Append assistant response to history
    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
