from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import os

app = Flask(__name__)
CORS(app)

# Fetch properties data from the API
def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# Load memory from external memory.txt file
def load_memory():
    with open("memory.txt", "r") as file:
        memory = file.read()
    return memory

# Set OpenAI API key from Render environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initial system prompts with more details
system_prompts = {
    "funny": "You are funny, humorous, playful, and outrageous. Use Indian context humor; say prices are over the roof!",
    "cranky": "You are cranky, irritated, sarcastic, and blunt. Use phrases like 'bhai khareedna hai toh batao'.",
    "formal": "You are formal, polite, professional, and helpful."
}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    properties = fetch_properties()

    formatted_properties = ""
    if properties and properties.get("data"):
        for prop in properties["data"]:
            name = prop.get('property_title', 'Property Name')
            locality = prop.get('project', {}).get('locality', 'Unknown location')
            price = prop.get('price')
            formatted_price = f"₹{price:,}" if (price := prop.get('price')) else "Price not disclosed"
            status = prop.get('property_status', 'Status unknown')
            url = prop.get('property_url', '#')

            formatted_properties += (
                f"✨ **{name}**\n"
                f"📍 Location: {locality}\n"
                f"💰 Price: {formatted_price(price)}\n"
                f"🚦 Status: {status}\n"
                f"🔗 [Visit for More Details:]({url})\n\n"
            )

    memory = ""
    try:
        with open('memory.txt', 'r') as file:
            formatted_memory = file.read().strip()
    except Exception as e:
        formatted_properties += "Property details unavailable at the moment."

    # Enhanced system prompt including memory and property details
    full_system_prompt = (
        f"{system_prompts.get(personality, 'formal')}\n\n"
        f"Memory Information:\n{open('memory.txt').read()}\n\n"
        f"Properties Available:\n{formatted_properties}\n\n"
        f"Use above memory and properties to answer user questions."
    )

    # Call GPT-4o model for generating replies
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content

    return jsonify({"reply": reply})

def formatted_price(price):
    if price is None:
        return "Price not disclosed"
    else:
        return f"₹{price:,.0f}"

if __name__ == '__main__':
    app.run(debug=True)
