from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import logging
import sys

app = Flask(__name__)
CORS(app)  

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("🚀 Starting Health Chatbot Server...")

# tải model
try:
    health_agent = pipeline("text2text-generation",model="google/flan-t5-base")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    health_agent = None

def create_health_prompt(question):
    return f"""You are a professional and friendly medical AI assistant.
Answer the user's question clearly, accurately, and concisely.
Provide suggestions, precautions, or explanations if relevant.
Do not give false information. Indicate if you are not sure.

User question: {question}
AI answer:"""

def create_translate_prompt(text):
    return f"""Translate the following text to French. Keep the medical terminology accurate and make it easy to understand for French speakers.

Text to translate: {text}

French translation:"""

def create_summary_prompt(text):
    return f"""Summarize the following medical text in French. Keep the key points, important advice, and recommendations. Make it concise but comprehensive.

Text to summarize: {text}

French summary:"""

@app.route("/", methods=["GET"])
def home():
    try:
        print("Bạn đã chạy API thành công!")
    except Exception as e:
        print(f"Error in home route: {e}")

@app.route("/ask", methods=["GET", "POST", "OPTIONS"])
def ask():
    try:
            data = request.get_json()
            user_question = data.get("question", "").strip()
            app.logger.info(f"Health question: {user_question[:100]}...")
            print(f"Processing health question: {user_question[:50]}...")
            prompt = create_health_prompt(user_question)
            result = health_agent(prompt, max_new_tokens=250, do_sample=True, temperature=0.7)
            answer = result[0]["generated_text"]
            
            app.logger.info(f"Health answer: {answer[:50]}...")
            print(f"Health answer sent: {answer[:50]}...")

            return jsonify({
                "answer": answer,
                "status": "success",
                "type": "health_advice"
            })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/translate", methods=["GET", "POST", "OPTIONS"])
def translate():
    try:
            data = request.get_json()
            text_to_translate = data.get("text", "").strip()
            app.logger.info(f"Translate request: {text_to_translate[:100]}...")
            print(f"Translating: {text_to_translate[:50]}...")
            prompt = create_translate_prompt(text_to_translate)
            result = health_agent(prompt, max_new_tokens=300, do_sample=True, temperature=0.3)
            translation = result[0]["generated_text"]
            
            app.logger.info(f"Translation: {translation[:50]}...")
            print(f"Translation sent: {translation[:50]}...")

            return jsonify({
                "answer": translation,
                "original_text": text_to_translate,
                "status": "success",
                "type": "translation"
            })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/summary", methods=["GET", "POST", "OPTIONS"])
def summary():
    try:
            data = request.get_json()
            text_to_summarize = data.get("text", "").strip()
            app.logger.info(f"Summary request: {text_to_summarize[:100]}...")
            print(f"Summarizing: {text_to_summarize[:50]}...")

            prompt = create_summary_prompt(text_to_summarize)
            result = health_agent(prompt, max_new_tokens=200, do_sample=True, temperature=0.3)
            summary_text = result[0]["generated_text"]
            
            app.logger.info(f"Summary: {summary_text[:50]}...")
            print(f"Summary sent: {summary_text[:50]}...")

            return jsonify({
                "answer": summary_text,
                "original_text": text_to_summarize,
                "status": "success",
                "type": "summary"
            })
        
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    try:
        return jsonify({
            "status": "healthy",
            "model_loaded": health_agent is not None,
            "server": "running",
            "endpoints": ["ask", "translate", "summary"]
        })
    except Exception as e:
        print(f"Error in health check: {e}")
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    try:
        app.run(
            host="0.0.0.0", 
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        sys.exit(1)