def normalize_phone(phone_number):
    """Normalize the phone number by removing the 'whatsapp:' prefix and any non-numeric characters."""
    if phone_number.startswith("whatsapp:"):
        phone_number = phone_number[len("whatsapp:"):]  # Remove the 'whatsapp:' prefix
    return phone_number
