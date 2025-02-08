import requests
import datetime
from whatsupApi import send_whatsapp_interactive_message
from rapidfuzz import process, fuzz
from database_connect_api import DatabaseHandler
from myfunction import get_user_location
from dotenv import load_dotenv
import random
import os
from twilio.rest import Client
import sys
sys.path.append("C:/Class/Python/AI/orders/")  # Adjust to your actual path
from logging_config import error_logger, orders_logger,chat_logger

# Load environment variables
load_dotenv()

class ProcessMessages:
    def __init__(self):
        self.intents = {
            "greeting": ["hello", "hi", "hey", "greetings", "good morning", "good evening"],
            "goodbye": ["bye", "goodbye", "see you", "take care", "exit"],
            "thanks": ["thank you", "thanks", "thankful", "appreciate", "thnks", "thnx"],
            "ask_time": ["time", "clock", "what time"],
            "ask_date": ["date", "day", "what date"],
            "fetch_orders": ["orders", "capex", "show orders", "latest orders"],
            "update_orders": ["approve", "update", "approve orders"],
            "joke": ["tell me a joke", "make me laugh", "funny", "joke"],
            "fetch_news": ["latest news", "news update", "what's happening", "current events"],
            "fetch_market": ["stock market", "market update", "latest stocks", "financial news"],
            "fetch_location": ["where am i", "my location", "get location", "fetch location"]
        }
        self.sid = os.getenv("TWILIO_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
             # Your WhatsApp number
        self.news_key=os.getenv("API_KEY1")

        self.db_handler = DatabaseHandler()
        self.user_id = None
        self.user_name = "User"
        self.user_dep = None
        self.user_phone = None
        self.user_desig = None
    
    def process_user_input(self, user_input, sender_phone):
        """Process user input and determine the response."""
        self.get_employee_details(sender_phone)
        if not self.user_id:
            return "Error: Employee ID not set. Please restart the program."
        
        user_input = user_input.strip().lower()
        commands = self.split_commands(user_input)
        responses = []
        greeting_response = ""  # Initialize an empty string for greeting
        goodbye_triggered = False  # Flag to track if goodbye has been triggered

        chat_logger.info(f"{self.user_name} ({self.user_phone}): {user_input}")        
        for command in commands:
            intents = self.get_intent(command)
            
            # Check for greeting intent
            if "greeting" in intents and not greeting_response:
                greeting_response = self.fetch_random_greeting()  # Set greeting only once
                
            # Check for goodbye intent and trigger only once
            if "goodbye" in intents and not goodbye_triggered:
                responses.append(self.say_goodbye())
                goodbye_triggered = True  # Ensure goodbye is only triggered once
            
            # Execute the corresponding functions for other intents
            if "goodbye" not in intents:  # Prevent adding multiple goodbyes
                responses.extend(self.execute_intent(intents))

        # Only include the greeting if it's the first command or hasn't been added yet
        if greeting_response and not any("greeting" in self.get_intent(cmd) for cmd in commands):
            return f"{greeting_response}\n" + "\n".join(responses)
        
        # If no goodbye intent, process the rest of the responses
        if not goodbye_triggered:
            return "\n".join(responses)
        else:
            chat_logger.info(f"BOT: {response_text}")
            return "\n".join(responses)



    def split_commands(self, user_input):
        """Split input into multiple commands if needed."""
        delimiters = [" and ", ",", "."]
        for delimiter in delimiters:
            if delimiter in user_input:
                return [cmd.strip() for cmd in user_input.split(delimiter) if cmd.strip()]
        return [user_input]

    def get_intent(self, message):
        """Determine the user's intent based on input."""
        message = message.lower()
        detected_intents = []
        all_keywords = {keyword: intent for intent, keywords in self.intents.items() for keyword in keywords}
        keywords = list(all_keywords.keys())
        match_result = process.extractOne(message, keywords, scorer=fuzz.ratio, score_cutoff=70)
        if match_result:
            match, score, _ = match_result
            detected_intents.append(all_keywords[match])
        return list(set(detected_intents)) or ["unknown"]

    def execute_intent(self, intents):
        """Execute the function corresponding to the detected intent."""
        intent_to_function = {
            "greeting": self.fetch_random_greeting,
            "goodbye": self.say_goodbye,
            "ask_time": self.show_time,
            "ask_date": self.show_date,
            "fetch_orders": self.fetch_orders,
            "update_orders": self.update_orders,
            "joke": self.tell_joke,
            "fetch_news": self.fetch_latest_news,
            "fetch_market": self.fetch_market_activity,
            "fetch_location": self.fetch_user_location,  # 
            "unknown": self.unknown_intent
        }
        responses = [intent_to_function.get(intent, self.unknown_intent)() for intent in intents]
        return responses

    def fetch_random_greeting(self):
        """Return a random greeting message."""
        greetings = [
            "Hello! How can I assist you today? 😊",
            "Hi there! What can I do for you? 👋",
            "Hey! How’s it going? 😄",
            "Greetings! How can I help? 🌟",
            "Good day! What can I help you with? 😊"
        ]
        return random.choice(greetings)

    def fetch_user_location(self):
        """Fetch and return the user's location with latitude and longitude."""
        location_data = get_user_location()
        
        if "error" in location_data:
            return location_data["error"]

        lat = location_data["latitude"]
        lon = location_data["longitude"]

        return (f"📍 You are in {location_data['city']}, {location_data['region']}, {location_data['country']}.\n"
                f"Coordinates: {lat}° N, {lon}° E 🌍")

    def say_goodbye(self):
        return f"Goodbye {self.user_name}! Take care and have an amazing day! 👋"

    def show_time(self):
        return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')} ⏰"

    def show_date(self):
        return f"Today’s date is {datetime.datetime.now().strftime('%d-%m-%Y')} 📅"

    def fetch_orders(self):
        """Fetch orders using stored Employee ID. Only managers can access."""
        if not self.user_id:
            return "Error: Employee ID not set. Please restart the program."

        # Fetch employee details
        employee_details = self.get_employee_details(self.user_phone)
        
        if not isinstance(employee_details, dict):
            return "Error: Failed to fetch valid employee details."

        # Check eligibility based on 'is_eligible'
        if not employee_details.get('is_eligible', False):
            return "❌ Access Denied: Only managers and directors can view orders."

        # Fetch department choice using the function from the same file
        department_option = get_user_department_choice(self.db_handler.dbConn)
        if department_option is None:
            return "Oops! Invalid choice. Please enter a valid department option. 🤔"

        # Log order request
        orders_logger.info(f"Employee {self.user_name} (ID: {self.user_id}) requested orders for department {department_option}.")
        
        # Fetch orders using department_option and employee details
        return self.db_handler.fetch_hd_orders(department_option, employee_details)
    def update_orders(self):
        """Update orders using stored Employee ID. Only managers can access."""
        if not self.user_id:
            return "Error: Employee ID not set. Please restart the program."

        employee_details = self.get_employee_details(self.user_phone)
        if not isinstance(employee_details, dict):
            return "Error: Failed to fetch valid employee details."
        if not employee_details.get('is_eligible', False):
            return "❌ Access Denied: Only managers and directors can update orders."

        department_option = get_user_department_choice(self.db_handler.dbConn)
        if department_option is None:
            return "Oops! Invalid choice. Please enter a valid department option. 🤔"

        orders_logger.info(f"Employee {self.user_name} (ID: {self.user_id}) updated orders for department {department_option}.")
        return self.db_handler.update_hd_orders(department_option)

    def tell_joke(self):
        """Fetch and return a random dad joke from an API."""
        joke_url = "https://icanhazdadjoke.com/"
        headers = {"Accept": "application/json"}

        try:
            response = requests.get(joke_url, headers=headers)
            data = response.json()

            if response.status_code == 200:
                return f"{data['joke']} 😄"
            else:
                return "Sorry, I couldn't fetch a dad joke at the moment. Try again later! 🤔"
        except Exception as e:
            return f"Error fetching joke: {str(e)}"


    def fetch_latest_news(self):
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": "ke",  # Use the correct country code (Kenya = "ke")
            "apiKey": self.news_key  # Use the API key from environment variables
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if response.status_code == 200 and data.get("articles"):
                articles = data['articles'][:5]  # Limit to top 5 articles
                news = "\n".join([f"{article['title']} - {article['source']['name']}" for article in articles])
                return f"Here are the latest trending news:\n{news}"
            else:
                return "Sorry, I couldn't fetch the latest news at the moment. Try again later! 🤔"
        except Exception as e:
            return f"Error fetching news: {str(e)}"
    def fetch_market_activity(self):
        return "The stock market is looking bullish today! 📊"

    def unknown_intent(self):
        return "Sorry, I didn’t quite catch that. Can you please clarify? 🤔"

    def get_employee_details(self, sender_phone):
        
        # sender_phone = normalize_phone(sender_phone)  # Normalize incoming phone number
        print(f"Checking phone number: {sender_phone}")  # Debugging print

        if not self.db_handler.dbConn:
            print("Error: Database connection not available.")
            return None

        try:
            emp_details = self.db_handler.fetch_employee_details(sender_phone)
            print(f"Database returned: {emp_details}")  # Debugging print

            if not emp_details:
                print("You are not registered with the company. Please contact HR to register.")
                return None

            self.user_phone = sender_phone
            self.user_id = emp_details['emp_id']
            self.user_name = f"{emp_details['first_name']} {emp_details['last_name']}"
            self.user_dep = emp_details['dept_id']
            self.user_desig = emp_details['desig_id']

            return emp_details
        except Exception as e:
            error_logger.error(f"Error in get_employee_details: {e}")
            return None



def main():
    bot = ProcessMessages()
    while True:
      # Example WhatsApp number (should come from Twilio)
        
        if bot.get_employee_details(sender_phone):
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print(bot.say_goodbye())
                break
            print(bot.process_user_input(user_input, sender_phone))
        else:
            print("Error: Could not fetch employee details. Please restart the program.")

if __name__ == "__main__":
    main()
