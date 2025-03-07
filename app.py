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
    return response.json()

# Load memory.txt content into a variable
with open("memory.txt", "r") as file:
    memory_content = file.read()

# Load your API key from Render environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    # Fetch properties data
    properties = fetch_properties()

    # Define enhanced personality-based prompts
    system_prompts = {
        "funny": "You're outrageously funny and playful, using quirky humor and local Indian references. Joke about property prices being through the roof and give humorous, lively responses.",
        "cranky": "You're cranky, impatient, and sarcastically blunt. Frequently question why the person wants to buy, and use phrases like 'bhai khareedna hai toh batao'.",
        "formal": "You're formal, polite, professional, and helpful. Provide clear, concise, and professional responses."
    }

    property_details = "Here are some properties currently available:\n"
    for prop in properties['results'][:5]:  # Limiting to first 5 properties for brevity
        property_details += f"- {prop['name']} at {prop['location']['name']} priced at ₹{prop['price']}\n"

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompts.get(personality, "formal")},
            {"role": "system", "content": memory_content},
            {"role": "system", "content": property_details},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)

