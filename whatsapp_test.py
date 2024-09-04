from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()

    if 'hola' in incoming_msg:
        msg.body("¡Hola! ¿Cómo estás?")
    else:
        msg.body("No entiendo tu mensaje. 😕 Intenta decir 'hola'.")

    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
