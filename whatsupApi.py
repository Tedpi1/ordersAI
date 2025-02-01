import json

def send_whatsapp_interactive_message(self, message_text):
    """Send a WhatsApp message with interactive buttons using Twilio API."""

    try:
        client = Client(self.sid, self.auth_token)

        # Send interactive message with buttons
        message = client.messages.create(
            to=self.my_whatsapp,
            from_=self.twilio_number,
            content_type="application/json",
            content=json.dumps({
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message_text
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "another_joke",
                                    "title": "😂 Another Joke"
                                }
                            },
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "stop_jokes",
                                    "title": "🚫 Stop Jokes"
                                }
                            }
                        ]
                    }
                }
            })
        )

        print("WhatsApp interactive joke message sent:", message.sid)

    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
