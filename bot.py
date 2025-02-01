import requests
import datetime
from rapidfuzz import process, fuzz
from database_connect_api import DatabaseHandler
from myfunction import get_user_department_choice
from dotenv import load_dotenv
import os
from twilio.rest import Client
import sys
sys.path.append("C:/Class/Python/AI/orders/")  # Adjust to your actual path
from logging_config import error_logger,orders_logger


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
            "fetch_orders": ["orders", "capex", "show orders", 
                "Give me Recent Orders", "What are the latest Orders", "What are the latest orders",
                "What orders does require my Appoval", "What are today Orders", "Which orders do we have today"
            ],
            "update_orders": ["approve", "update", "approve orders"],
            "joke": ["tell me a joke", "make me laugh", "funny", "joke"],
            "fetch_news": ["latest news", "news update", "what's happening", "current events"],
            "fetch_market": ["stock market", "market update", "latest stocks", "financial news"]
        }
        self.sid = os.getenv("TWILIO_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.my_whatsapp = "whatsapp:+254782793348"  # Your WhatsApp number

        self.db_handler = DatabaseHandler()
        self.user_id = None
        self.user_name = "User"
        self.user_dep = None
        self.user_desig = None
        self.get_employee_details()

    def process_user_input(self, user_input):
        """Process user input and determine the response."""
        user_input = user_input.strip().lower()
        commands = self.split_commands(user_input)
        responses = []
        for command in commands:
            intents = self.get_intent(command)
            responses.extend(self.execute_intent(intents))
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
            "fetch_orders": self.fetch_orders,  # ✅ Removed emp_id
            "update_orders": self.update_orders,
            "joke": self.tell_joke,
            "fetch_news": self.fetch_latest_news,
            "fetch_market": self.fetch_market_activity,
            "unknown": self.unknown_intent
        }
        responses = [intent_to_function.get(intent, self.unknown_intent)() for intent in intents]
        return responses



    def fetch_random_greeting(self):
        """Return a random greeting. Accessible to any employee."""
        return "Hello! How can I assist you today? 😊"

    def say_goodbye(self):
        return f"Goodbye {self.user_name}! Take care and have an amazing day! 👋"

    def show_time(self):
        return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')} ⏰"

    def show_date(self):
        return f"Today’s date is {datetime.datetime.now().strftime('%d-%m-%Y')} 📅"

    def fetch_orders(self):
        """Fetch orders using stored Employee ID."""
        if not self.user_id:
            return "Error: Employee ID not set. Please restart the program."

        employee_details = self.get_employee_details()
        if not isinstance(employee_details, dict):
            return "Error: Failed to fetch valid employee details."
        if not employee_details['is_eligible']:
            return "You do not have the required designation to approve orders."

        department_option = get_user_department_choice(self.db_handler.dbConn)
        if department_option is None:
            return "Oops! Invalid choice. Please enter a valid department option. 🤔"

        orders_logger.info(f"Employee {self.user_name} (ID: {self.user_id}) requested orders for department {department_option}.")
        return self.db_handler.fetch_hd_orders(department_option, employee_details)

    def update_orders(self):
        """Update orders using stored Employee ID."""
        if not self.user_id:
            return "Error: Employee ID not set. Please restart the program."

        employee_details = self.get_employee_details()
        if not employee_details or not employee_details.get('is_eligible', False):
            return "You do not have the required designation to approve orders."

        department_option = get_user_department_choice(self.db_handler.dbConn)
        if department_option is None:
            return "Oops! Invalid choice. Please enter a valid department option. 🤔"

        orders_logger.info(f"Employee {self.user_name} (ID: {self.user_id}) updated orders for department {department_option}.")
        return self.db_handler.update_hd_orders(department_option)

    def tell_joke(self):
        """Return a joke. Accessible to any employee."""
        return "Why don't skeletons fight each other? They don't have the guts! 😄"

    def fetch_latest_news(self):
        """Return the latest news. Accessible to any employee."""
        return "The latest news is: Python programming continues to rise in popularity! 📈"

    def fetch_market_activity(self):
        """Return market activity details. Accessible to any employee."""
        return "The stock market is looking bullish today! 📊"

    def unknown_intent(self):
        return "Sorry, I didn’t quite catch that. Can you please clarify? 🤔"

    def get_employee_details(self):
        """Fetch and store employee details once when the program starts."""
        if self.user_id is not None:
            # If user_id is already set, return existing details
            return {
                "emp_id": self.user_id,
                "first_name": self.user_name.split()[0],
                "last_name": self.user_name.split()[1] if " " in self.user_name else "",
                "dept_id": self.user_dep,
                "desig_id": self.user_desig,
                "is_eligible": self.user_desig in [33, 25, 34]  # Farm Manager, Production Manager, Director
            }

        if not self.db_handler.dbConn:
            print("Error: Database connection not available.")
            exit()

        while True:
            try:
                emp_id = input("Enter your Employee ID: ").strip()
                if not emp_id.isdigit():
                    print("Invalid input. Please enter a numeric Employee ID.")
                    continue
                
                emp_details = self.db_handler.fetch_employee_details(emp_id)
                if emp_details:
                    self.user_id = int(emp_id)
                    self.user_name = f"{emp_details['first_name']} {emp_details['last_name']}"
                    self.user_dep = emp_details['dept_id']
                    self.user_desig = emp_details['desig_id']
                    
                    print(f"Welcome, {self.user_name}! 🎉")
                    return emp_details  # Return details dictionary
                else:
                    print("Sorry, you must be a Farm Manager, Production Manager, or Director to approve orders.")
            except Exception as e:
                error_logger.error(f"Error in get_employee_details: {e}")
                print(f"Error: {e}")
                exit()

def main():
    bot = ProcessMessages()
    print("Welcome! Type your query or 'exit' to quit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print(bot.say_goodbye())
            break
        response = bot.process_user_input(user_input)
        print(response)

if __name__ == "__main__":
    main()
