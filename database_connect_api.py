import mysql.connector
from mysql.connector import Error
from tabulate import tabulate

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

    def fetch_employee_details(self, phone_no):
        """Fetch employee details and set eligibility based on designation."""
        if not self.dbConn:
            return None
        try:
            cursor = self.dbConn.cursor(dictionary=True)
            query = """
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
                LEFT JOIN ja_db.hrm_departments hd ON h.emp_id = hd.dept_id
                LEFT JOIN ja_db.hrm_designations d ON h.desig_id = d.desig_id
                WHERE h.phone_no = %s
            """
            cursor.execute(query, (phone_no,))
            employee_details = cursor.fetchone()
            
            if employee_details:
                # Set eligibility based on desig_id (33 = Manager, 25 = Director, 34 = another role)
                employee_details['is_eligible'] = employee_details['desig_id'] in [33, 25, 34]

            return employee_details
        except mysql.connector.Error as e:
            error_logger.error(f"Database error in fetch_employee_details: {e}")
            return None



def get_user_department_choice(dbConn):
    """
    Display a menu for the user to choose a department, sourced from the database,
    and return their choice (department name or "ALL DEPARTMENTS").
    The user can input either the department name or its numeric position.
    """
    if not dbConn:
        print("Database connection failed. Please check your connection settings.")
        return None

    try:
        # Fetch all department names from the database
        cursor = dbConn.cursor()
        cursor.execute("SELECT distinct(department) FROM orders_departments")
        departments = cursor.fetchall()

        if not departments:
            print("No departments found in the database.")
            return None

        # Create a mapping of the department names to the indices
        department_mapping = {idx + 1: dept[0] for idx, dept in enumerate(departments)}  # dept[0] gives the department name

        # Format and display the department options in five columns
        print("Select a department to fetch approved orders:")
        department_items = list(department_mapping.items())
        column_width = max(len(dept[0]) for dept in departments) + 3  # Adjust spacing for alignment
        num_columns = 5  # Number of columns
        num_rows = (len(department_items) + num_columns - 1) // num_columns  # Calculate rows needed

        # Print the department options in rows and columns
        for row in range(num_rows):
            row_output = []
            for col in range(num_columns):
                index = row + col * num_rows
                if index < len(department_items):
                    item_num, dept_name = department_items[index]
                    row_output.append(f"{item_num}. {dept_name:<{column_width}}")
                else:
                    row_output.append(" " * (column_width + 4))  # Empty space for alignment
            print(" ".join(row_output))

        # Add the option for "ALL DEPARTMENTS"
        print(f"{len(department_mapping) + 1}. ALL DEPARTMENTS")

        # Get user choice (either department name or numeric index)
        user_input = input(f"Enter your choice (1-{len(department_mapping) + 1} or department name): ").strip()

        # Check if the user input is a valid department name
        if user_input.lower() == "all departments":
            return "ALL DEPARTMENTS"

        # Check if the input is a valid numeric choice
        if user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= len(department_mapping) + 1:
                if choice == len(department_mapping) + 1:
                    return "ALL DEPARTMENTS"
                return department_mapping[choice]
            else:
                print("Invalid numeric choice. Please select a valid department.")
                return None
        else:
            # Check if the input matches any department name
            for dept_name in department_mapping.values():
                if user_input.lower() == dept_name.lower():
                    return dept_name
            print("Invalid department name. Please enter a valid name or numeric choice.")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None






