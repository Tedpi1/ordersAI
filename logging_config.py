import logging

# Configure error logging
logging.basicConfig(filename="errors.log",
                    level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(message)s")

error_logger = logging.getLogger("error_logger")

# Configure order requests logging
orders_logger = logging.getLogger("orders_logger")
order_handler = logging.FileHandler("orders.log")
order_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
orders_logger.addHandler(order_handler)
orders_logger.setLevel(logging.INFO)

# Configure chat history logging
chat_logger = logging.getLogger("chat_logger")
chat_handler = logging.FileHandler("chat_history.log")  # This file stores chat history
chat_handler.setFormatter(logging.Formatter("%(asctime)s - USER: %(message)s"))
chat_logger.addHandler(chat_handler)
chat_logger.setLevel(logging.INFO)
