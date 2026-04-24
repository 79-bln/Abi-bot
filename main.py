import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15,
        )
    except Exception as e:
        print(f"Telegram send_message error: {e}")


@app.route("/", methods=["GET"])
def home():
    return "Bot läuft"


@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}

    message = update.get("message") or update.get("edited_message")
    if not message:
        return "ok", 200

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    user_text = message.get("text")

    if not chat_id or not user_text:
        return "ok", 200

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": "Du bist ein hilfreicher, kurzer Telegram-Assistent."},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.7,
    }

    try:
        r = requests.post(
            OPENAI_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
    except Exception as e:
        print(f"OpenAI request error: {e}")
        send_message(chat_id, "Fehler beim Verbinden mit OpenAI.")
        return "ok", 200

    if not r.ok:
        print("OpenAI HTTP error:", r.status_code, r.text)
        send_message(chat_id, "OpenAI hat einen Fehler zurückgegeben.")
        return "ok", 200

    try:
        data = r.json()
    except Exception:
        print("OpenAI returned non-JSON:", r.text)
        send_message(chat_id, "Ungültige Antwort von OpenAI.")
        return "ok", 200

    choices = data.get("choices")
    if not choices:
        print("OpenAI response without choices:", data)
        send_message(chat_id, "Die OpenAI-Antwort war unerwartet.")
        return "ok", 200

    answer = choices[0]["message"]["content"]
    send_message(chat_id, answer)

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
