import mysql.connector
from mysql.connector import Error
from tabulate import tabulate
from myfunction import get_user_department_choice
from logging_config import error_logger  # Import error logger
from dotenv import load_dotenv
import os


class DatabaseHandler:
    def __init__(self, host="localhost", database="ja_db", user="root", password="2044"):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.dbConn = self.connect_to_database()

    def connect_to_database(self):
        """Establish a connection to the MySQL database."""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
            )
            if connection.is_connected():
                return connection
        except Error as e:
            error_logger.error(f"Database connection error: {e}")
            return None

    def update_hd_orders(self, department_option):
        """Update orders based on department selection with LEFT JOIN."""
        if not self.dbConn:
            return "Database connection failed. Please check your connection settings."
        try:
            cursor = self.dbConn.cursor()
            if department_option == "ALL DEPARTMENTS":
                query = """
                UPDATE orders_internal_orders o
                LEFT JOIN orders_departments d ON o.dept_id = d.dept_id
                SET o.hd_approved = 0
                WHERE o.hd_approved = 1
                  AND o.md_approved = 1 
                  AND o.capex_id = 0
                """
                cursor.execute(query)
            else:
                query = """
                UPDATE orders_internal_orders o
                LEFT JOIN orders_departments d ON o.dept_id = d.dept_id
                SET o.md_approved = 0
                WHERE o.hd_approved = 0
                  AND o.md_approved = 1 
                  AND o.capex_id = 0
                  AND department = %s
                """
                cursor.execute(query, (department_option,))
            
            self.dbConn.commit()
            affected_rows = cursor.rowcount
            if affected_rows == 0:
                return f"No orders found for {department_option} to update."
            return f"{affected_rows} records updated successfully for {department_option}."
        except Error as e:
            error_logger.error(f"Error updating orders: {e}")
            return f"Error updating orders: {str(e)}"

    def fetch_name(self):
        """Fetch name of the Bot User from the database."""
        if not self.dbConn:
            return "Database connection failed. Please check your connection"
        try:
            cursor = self.dbConn.cursor()
            cursor.execute("SELECT first_name as Username FROM ja_db.hrm_employees WHERE emp_id=476")
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return "Username not found"
        except Error as e:
            error_logger.error(f"Error fetching username: {e}")
            return f"Error fetching username: {str(e)}"

    def format_table(self, records, headers):
        """Format the table for terminal output."""
        return tabulate(
            records,
            headers=headers,
            tablefmt="grid",
            stralign="center",
            numalign="right"
        )

    def fetch_hd_orders(self, department_option, employee_details):
        """
        Fetch orders based on department selection and ensure the user is eligible 
        to approve orders.
        """
        if not self.dbConn:
            return "Database connection failed. Please check your connection settings."
        if not employee_details:
            return "Employee not found or does not have permission to approve orders."
        if not employee_details['is_eligible']:
            return "You do not have the required designation to approve orders."
        try:
            cursor = self.dbConn.cursor()
            if department_option == "ALL DEPARTMENTS":
                query = """
                    SELECT o.int_order_id, o.order_date, o.item_name, o.qty_ordered 
                    FROM orders_internal_orders o 
                    LEFT JOIN orders_departments USING(dept_id)
                    WHERE hd_approved = 1 AND md_approved = 0 AND capex_id = 0
                """
                cursor.execute(query)
            else:
                query = """
                    SELECT o.int_order_id, o.order_date, o.item_name, o.qty_ordered 
                    FROM orders_internal_orders o 
                    LEFT JOIN orders_departments USING(dept_id)
                    WHERE hd_approved = 1 AND md_approved = 0 AND capex_id = 0 AND department = %s
                """
                cursor.execute(query, (department_option,))
            results = cursor.fetchall()
            if not results:
                return "No pending orders found for the selected department."
            total_records = len(results)
            print(f"{total_records} records found. How many would you like to print?")
            while True:
                try:
                    num_to_print = int(input("Enter the number of records to print: "))
                    if 0 <= num_to_print <= total_records:
                        break
                    else:
                        print(f"Please enter a number between 0 and {total_records}.")
                except ValueError:
                    print("Please enter a valid number.")
            records_to_print = results[:num_to_print]
            headers = ["Item id", "Order Date", "Item Name", "Quantity Ordered"]
            return self.format_table(records_to_print, headers)
        except mysql.connector.Error as e:
            error_logger.error(f"Error fetching orders: {e}")
            return f"Error fetching orders: {str(e)}"

    def fetch_employee_details(self, emp_id):
        """
        Fetch employee details based on Employee ID and check if they can approve orders.
        """
        if not self.dbConn:
            return None
        try:
            cursor = self.dbConn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    h.emp_id, 
                    h.first_name, 
                    h.last_name,
                    h.phone_no,
                    d.designation,
                    d.desig_id,
                    hd.department,
                    hd.dept_id
                FROM ja_db.hrm_employees h
                LEFT JOIN ja_db.hrm_designations d USING (desig_id)
                LEFT JOIN ja_db.hrm_departments hd USING (dept_id)
                WHERE h.emp_id = %s
                  AND hd.dept_id = 1
                  AND (d.desig_id = 33 OR d.desig_id = 25 OR d.desig_id = 34);
            """, (emp_id,))
            result = cursor.fetchone()
            if result:
                is_eligible = result['desig_id'] in [33, 25, 34]
                return {**result, 'is_eligible': is_eligible}
            else:
                return None
        except mysql.connector.Error as e:
            error_logger.error(f"Database error in fetch_employee_details: {e}")
            return None
