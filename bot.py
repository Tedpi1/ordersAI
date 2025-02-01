import requests
import random
import datetime
from rapidfuzz import process, fuzz
from database_connect_api import DatabaseHandler
from myfunction import get_user_department_choice
from dotenv import load_dotenv
import os
from twilio.rest import Client
from chatGptresponse import gptRespond 

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
                "Give me Recent Orders", "What are the latest Orders","What are the latest orders",
                "What orders does require my Appoval", 
                "What are today Orders","Which orders do we have today"
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
            "fetch_orders": self.fetch_orders,
            "update_orders": self.update_orders,
            "joke": self.tell_joke,
            "fetch_news": self.fetch_latest_news,
            "fetch_market": self.fetch_market_activity,
            "unknown": self.unknown_intent
        }
        responses = [intent_to_function.get(intent, self.unknown_intent)() for intent in intents]
        return responses

    def fetch_random_greeting(self):
        """Fetch a random greeting from an API."""
        try:
            response = requests.get("https://api.greeting.com/")  # Replace with your actual API URL
            if response.status_code == 200:
                greeting_data = response.json()
                return greeting_data.get("greeting", "Hello! How can I assist you today?")
            else:
                return "Hello! How can I assist you today? "
        except requests.exceptions.RequestException:
            return "Hello! How can I assist you today? "

    def greet(self):
        """Generate a greeting message using a random API."""
        greeting = self.fetch_random_greeting()
        return f"{greeting} 😊"

    def say_goodbye(self):
        return f"Goodbye {self.user_name}! Take care and have an amazing day! 👋"

    def show_time(self):
        return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')} ⏰"

    def show_date(self):
        return f"Today’s date is {datetime.datetime.now().strftime('%d-%m-%Y')} 📅"

    def fetch_orders(self):
        department_option = get_user_department_choice(self.db_handler.dbConn)
        if department_option is None:
            return "Oops! Invalid choice. Please enter a valid department option. 🤔"
        return self.db_handler.fetch_hd_orders(department_option)

    def update_orders(self):
        department_option = get_user_department_choice(self.db_handler.dbConn)
        if department_option is None:
            return "Oops! Invalid choice. Please enter a valid department option. 🤔"
        return self.db_handler.update_hd_orders(department_option)

    def get_employee_details(self):
        """Prompt user for Employee ID and fetch details from connect_api."""
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
                    

                    print(f"Welcome, {self.user_name}! 🎉")
                    return self.user_id
                else:
                    print("Sorry, but you must be registered in the Management department")
            except Exception as e:
                print(f"Error: {e}")
                exit()
    
    
    def unknown_intent(self):
        return "Sorry, I didn’t quite get that. Can you please rephrase? 🤖"

    def tell_joke(self):
        """Fetch a random joke and send it via WhatsApp."""
        joke_url = "https://official-joke-api.appspot.com/random_joke"
        
        try:
            response = requests.get(joke_url)
            joke_data = response.json()
            joke_text = f"{joke_data['setup']} - {joke_data['punchline']} 😄"

            # Send the joke via WhatsApp
            self.send_whatsapp_message(joke_text)

            return joke_textexit
        except requests.exceptions.RequestException:
            return "Sorry, I couldn’t fetch a joke at the moment. Try again later. 😕"


    def fetch_latest_news(self):
        """Fetch latest news headlines with source links."""
        api_key = os.getenv("API_KEY1")  # Ensure this key is stored in .env
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
        
        try:
            response = requests.get(url)
            news_data = response.json()
            if news_data.get("status") == "ok":
                top_articles = news_data.get("articles", [])[:3]
                headlines = "\n".join([f"{idx+1}. {article.get('title', 'No title')}\n   Source: {article.get('url', 'No link')}" for idx, article in enumerate(top_articles)])
                return f"Here are the latest news headlines:\n{headlines}"
            else:
                return "Sorry, I couldn't fetch the latest news at the moment. 😔"
        except requests.exceptions.RequestException:
            return "Sorry, there was an error fetching the news. Please try again later. 😞"

    def fetch_market_activity(self):
        """Fetch latest stock market updates with source links."""
        api_key = os.getenv("API_KEY")  # Ensure API key is stored in .env
        url = f"https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={api_key}"
        
        try:
            response = requests.get(url)
            market_data = response.json()

            if "top_gainers" in market_data:
                top_gainers = market_data["top_gainers"][:3]
                gainers_info = "\n".join([f"{stock.get('ticker', 'N/A')}: {stock.get('price', 'N/A')} ({stock.get('change_percent', '0')}%)\n   Source: https://www.alphavantage.co/" for stock in top_gainers])
                return f"Here are the top market gainers:\n{gainers_info}"
            else:
                return "Sorry, I couldn't fetch the market data at the moment. 😕"
        except requests.exceptions.RequestException:
            return "Sorry, there was an error fetching market data. Please try again later. 😔"


    def send_whatsapp_message(self, message_body):
        """Send a message to WhatsApp using Twilio."""
        try:
            client = Client(self.sid, self.auth_token)
            message = client.messages.create(
                to=self.my_whatsapp,
                from_=self.twilio_number,
                body=message_body
            )
            print(f"WhatsApp message sent! Message SID: {message.sid}")
        except Exception as e:
            print(f"Error sending WhatsApp message: {e}")

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
