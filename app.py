from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import requests
import os

app = Flask(__name__)
CORS(app)

def fetch_properties():
    url = "https://api.ivy.homes/api/v2/properties/?property_status=For%20Sale&property_status=Coming%20Soon"
    response = requests.get(url)
    return response.json().get('data', [])

try:
    with open("memory.txt", "r") as file:
        memory_content = file.read()
except Exception as e:
    memory_content = "Memory data not loaded."
    print(f"Error loading memory.txt: {e}")

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality', 'formal')
    user_message = data.get('message')

    try:
        properties = fetch_properties()
        property_details = "Available Properties:\n"
        for prop in properties:
            name = prop.get('property_title', 'Unnamed')
            locality = prop['project'].get('locality', 'Unknown locality')
            price = f"₹{prop['price']}" if prop['price'] else "Price not disclosed"
            status = prop.get('property_status', 'Status unknown')
            url = prop.get('property_url', '#')
            property_details += f"- {name} in {locality}, {price}, Status: {status}. More info: {url}\n"

        system_prompts = {
            "funny": "You're outrageously funny and playful, using quirky humor and local Indian references. Joke about property prices being through the roof and give humorous, lively responses.",
            "cranky": "You're cranky, impatient, and sarcastically blunt. Frequently question why the person wants to buy, and use phrases like 'bhai khareedna hai toh batao'.",
            "formal": "You're formal, polite, professional, and helpful. Provide clear, concise, and professional responses."
        }

        full_system_message = (
            f"{system_prompts.get(personality, 'formal')}\n\n"
            f"{memory_content}\n\n"
            f"{property_details}\n\n"
            "Use the above details to specifically answer queries about available properties, prices, and locations."
        )

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": full_system_message},
                {"role": "user", "content": user_message}
            ]
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        print(f"Error in chat route: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

