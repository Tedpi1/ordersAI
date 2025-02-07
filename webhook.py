from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from bot import ProcessMessages  # Import your bot logic
from myfunction import normalize_phone

app = Flask(__name__)
bot = ProcessMessages()  # Initialize the bot

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming WhatsApp messages from Twilio."""
    incoming_msg = request.values.get("Body", "").strip().lower()
    sender_phone = request.values.get("From", "")
    sender_phone = normalize_phone(sender_phone)  # Normalize the phone number

    print(f"Message received: {incoming_msg} from {sender_phone}")

    # Process the user input using the bot logic
    response_text = bot.process_user_input(incoming_msg, sender_phone)

    # Send a response back to the user
    twilio_response = MessagingResponse()
    twilio_response.message(response_text)

    return str(twilio_response)



if __name__ == "__main__":
    app.run(port=5000, debug=True)
