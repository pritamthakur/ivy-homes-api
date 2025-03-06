from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os  # clearly import os for environment variables

app = Flask(__name__)
CORS(app)

# Load your memory file clearly into a variable at startup
with open("memory.txt", "r") as file:
    ivy_memory = file.read()

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    personality = data.get('personality')
    user_message = data.get('message')

    system_prompts = {
        "funny": "You are funny, humorous, and playful.",
        "cranky": "You are cranky, irritated, and sarcastic.",
        "formal": "You are formal, polite, and professional."
    }

    system_instruction = system_prompts.get(personality, "You are formal and polite.")

    full_system_prompt = f"{system_instruction}\n\nContext about Ivy Homes:\n{ivy_memory}"

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # clearly fetch from env variable

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content.strip()

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)

