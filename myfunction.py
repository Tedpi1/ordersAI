import requests


def normalize_phone(phone_number):
    """Normalize the phone number by removing the 'whatsapp:' prefix and any non-numeric characters."""
    if phone_number.startswith("whatsapp:"):
        phone_number = phone_number[len("whatsapp:"):]  # Remove the 'whatsapp:' prefix
    return phone_number


def get_user_location():
    """Fetch the user's approximate location based on their IP address."""
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()

        if response.status_code == 200:
            city = data.get("city", "Unknown city")
            region = data.get("region", "Unknown region")
            country = data.get("country", "Unknown country")
            loc = data.get("loc", "Unknown location")  # Example: "37.7749,-122.4194"

            # Ensure loc is valid before splitting
            latitude, longitude = loc.split(",") if "," in loc else ("Unknown", "Unknown")

            return {
                "city": city,
                "region": region,
                "country": country,
                "latitude": latitude,
                "longitude": longitude
            }
        else:
            return {"error": "Could not retrieve location data"}
    except Exception as e:
        return {"error": f"Error fetching location: {str(e)}"}