from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import requests
import os

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Fetch properties data
def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    return response.json().get('data', [])

# Load memory content
with open("memory.txt", "r") as file:
    memory_content = file.read()

# Store chat history globally
chat_history = []

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    properties = fetch_properties()

    # Prepare formatted property details
property_details = "🏡 Available Properties:\n\n"
for prop in properties:
    name = prop.get('property_title', 'Unnamed')
    locality = prop['project'].get('locality', 'Unknown locality')
    price = f"₹{prop['price']:,}" if prop['price'] else "Price not disclosed"
    status = prop.get('property_status', 'Status unknown')
    url = prop.get('property_url', '#')

    property_details += (
        f"✨ **{name}**\n"
        f"📍 Location: {locality}\n"
        f"💰 Price: {price}\n"
        f"🚦 Status: {status}\n"
        f"🔗 [More Info]({url})\n\n"
    )

    # Personality definitions
    system_prompts = {
        "funny": "You're outrageously funny, playful, and use quirky humor and Indian references. Joke about property prices being through the roof!",
        "cranky": "You're cranky, impatient, and sarcastic. Say things like 'bhai khareedna hai toh batao', showing humorous impatience.",
        "formal": "You're formal, polite, professional, clear, and helpful."
    }

    # Full system prompt with property and memory context
    full_system_message = (
        f"{system_prompts.get(personality, 'formal')}\n\n"
        f"{memory_content}\n\n"
        f"{property_details}\n"
        "Use these details specifically to answer queries about properties, prices, and locations."
    )

    # Append new user message to the chat history
    chat_history.append({"role": "user", "content": user_message})

    # Complete conversation history sent to OpenAI
    messages = [{"role": "system", "content": full_system_message}] + chat_history

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Save assistant's response to history
    chat_history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
