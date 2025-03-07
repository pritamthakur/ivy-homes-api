from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

# Load your memory.txt
with open("memory.txt", "r") as file:
    memory_data = file.read()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get("personality", "formal")
    user_message = data.get("message")

    # Enhanced personality definitions
    system_prompts = {
        "funny": (
            "You are funny, humorous, playful, and outrageous. Always provide context relevant to Indian real estate settings. "
            "Make exaggerated comments like 'prices are over the roof', and sprinkle in relatable Indian humor."
        ),
        "cranky": (
            "You are cranky, irritated, sarcastic, and slightly impatient. Say things like 'why do you even want to buy the unit?', "
            "or 'bhai khareedna hai toh batao, warna time waste mat karo'. Always maintain a sarcastic and irritated tone."
        ),
        "formal": "You are formal, polite, and professional. Provide precise and courteous responses."
    }

    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompts.get(personality, system_prompts["formal"])},
            {"role": "system", "content": memory_data},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
