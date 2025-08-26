from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import unicodedata
import re
import os

app = Flask(__name__)
CORS(app)

def load_model_with_fallback():
    model_configs = [
        lambda: pipeline("text2text-generation", model="google/flan-t5-base", device=-1),
        lambda: pipeline("text2text-generation", model="google/flan-t5-small", device=-1),
        lambda: pipeline("text2text-generation", model="google/flan-t5-base")
    ]
    
    for config in model_configs:
        try:
            return config()
        except:
            continue
    return None

health_agent = load_model_with_fallback()

def normalize_text(text):
    try:
        text = unicodedata.normalize('NFC', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except:
        return text

def create_health_prompt(question):
    return f"""You are a professional medical AI assistant. Provide comprehensive medical advice and health information.

Guidelines:
1. Answer clearly, accurately, and professionally
2. Use simple, understandable language
3. Provide practical suggestions and recommendations
4. Include relevant precautions and warnings when necessary
5. If uncertain, clearly state your limitations
6. Encourage consulting healthcare professionals for serious conditions

USER QUESTION: {normalize_text(question)}

MEDICAL ADVICE:"""

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Health Chatbot API",
        "version": "3.0",
        "status": "running",
        "model_loaded": health_agent is not None
    })

@app.route("/ask", methods=["POST"])
def ask():
    if not health_agent:
        return jsonify({"error": "Model not loaded", "status": "error"}), 503
        
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Missing question field", "status": "error"}), 400
        
    user_question = data.get("question", "").strip()
    if not user_question:
        return jsonify({"error": "Question cannot be empty", "status": "error"}), 400
    
    try:
        prompt = create_health_prompt(user_question)
        result = health_agent(
            prompt, 
            max_new_tokens=300, 
            do_sample=True, 
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1
        )
        
        answer = normalize_text(result[0]["generated_text"].strip())
        
        return jsonify({
            "answer": answer,
            "question": user_question,
            "status": "success",
            "type": "health_advice"
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/translate", methods=["POST"])
def translate():
    if not health_agent:
        return jsonify({"error": "Model not loaded", "status": "error"}), 503
        
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing text field", "status": "error"}), 400
        
    text_to_translate = data.get("text", "").strip()
    target_lang = data.get("target_language", "French")
    
    if not text_to_translate:
        return jsonify({"error": "Text cannot be empty", "status": "error"}), 400
    
    try:
        prompt = f"Translate to {target_lang}: {text_to_translate}\n\n{target_lang} translation:"
        
        result = health_agent(
            prompt, 
            max_new_tokens=400, 
            do_sample=True, 
            temperature=0.3,
            top_p=0.8,
            repetition_penalty=1.1
        )
        
        translation = normalize_text(result[0]["generated_text"].strip())
        
        if not translation or translation == text_to_translate:
            translation = f"[{target_lang}] " + text_to_translate
        
        return jsonify({
            "answer": translation,
            "original_text": text_to_translate,
            "target_language": target_lang,
            "status": "success",
            "type": "translation"
        })
    except Exception as e:
        return jsonify({
            "answer": f"[{target_lang}] " + text_to_translate,
            "original_text": text_to_translate,
            "target_language": target_lang,
            "status": "partial_success",
            "type": "translation",
            "error": str(e)
        })

@app.route("/summary", methods=["POST"])
def summary():
    if not health_agent:
        return jsonify({"error": "Model not loaded", "status": "error"}), 503
        
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing text field", "status": "error"}), 400
        
    text_to_summarize = data.get("text", "").strip()
    target_lang = data.get("target_language", "French")
    
    if not text_to_summarize:
        return jsonify({"error": "Text cannot be empty", "status": "error"}), 400
    
    try:
        prompt = f"Summarize this medical text in {target_lang}: {text_to_summarize}\n\n{target_lang} summary:"
        
        result = health_agent(
            prompt, 
            max_new_tokens=300, 
            do_sample=True, 
            temperature=0.4,
            top_p=0.8,
            repetition_penalty=1.2
        )
        
        summary_text = normalize_text(result[0]["generated_text"].strip())
        
        if not summary_text:
            summary_text = f"[{target_lang} Summary] " + text_to_summarize[:200] + "..."
        
        return jsonify({
            "answer": summary_text,
            "original_text": text_to_summarize,
            "target_language": target_lang,
            "status": "success",
            "type": "summary"
        })
    except Exception as e:
        return jsonify({
            "answer": f"[{target_lang} Summary] " + text_to_summarize[:200] + "...",
            "original_text": text_to_summarize,
            "target_language": target_lang,
            "status": "partial_success",
            "type": "summary",
            "error": str(e)
        })

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "model_loaded": health_agent is not None,
        "version": "3.0"
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
