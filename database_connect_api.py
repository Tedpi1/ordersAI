import mysql.connector
from mysql.connector import Error
from tabulate import tabulate
from myfunction import get_user_department_choice  # Remove this if not needed here

class DatabaseHandler:
    def __init__(
        self, host="localhost", database="ja_db", user="root", password="2044"
    ):
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
            print(f"Error: {e}")
            return None

    def fetch_hd_orders(self, department_option, emp_id):
        """Fetch orders based on department selection and ensure the user is eligible to approve orders."""
        if not self.dbConn:
            return "Database connection failed. Please check your connection settings."

        # First, fetch the employee details to check if they are eligible
        employee_details = self.fetch_employee_details(emp_id)

        if not employee_details:
            return "Employee not found or does not have permission to approve orders."

        if not employee_details['is_eligible']:
            return "You do not have the required designation to approve orders."

        try:
            cursor = self.dbConn.cursor()

            # Define the table and query based on department selection
            if department_option == "ALL DEPARTMENTS":
                query = """
                    SELECT 
                        o.int_order_id, o.order_date, o.item_name, o.qty_ordered 
                    FROM orders_internal_orders o 
                    LEFT JOIN orders_departments using(dept_id)
                    WHERE hd_approved=1 and md_approved=0 and capex_id=0
                """
                cursor.execute(query)
            else:
                query = """
                    SELECT 
                        o.int_order_id, o.order_date, o.item_name, o.qty_ordered 
                    FROM orders_internal_orders o 
                    LEFT JOIN orders_departments using(dept_id)
                    WHERE hd_approved=1 and md_approved=0 and capex_id=0 and department = %s
                """
                cursor.execute(query, (department_option,))

            # Fetch all rows
            results = cursor.fetchall()

            if not results:
                return "No pending orders found for the selected department."

            # Notify the user of the number of records
            total_records = len(results)
            print(f"{total_records} records found. How many would you like to print?")

            # Get user input for the number of records to print
            while True:
                try:
                    num_to_print = int(input("Enter the number of records to print: "))
                    if 0 <= num_to_print <= total_records:
                        break
                    else:
                        print(f"Please enter a number between 0 and {total_records}.")
                except ValueError:
                    print("Please enter a valid number.")

            # Print the specified number of records
            records_to_print = results[:num_to_print]

            # Format the results into a table
            headers = [
                "Item id", "Order Date", "Item Name", "Quantity Ordered"
            ]
            return self.format_table(records_to_print, headers)

        except mysql.connector.Error as e:
            return f"Error fetching orders: {str(e)}"

    def update_hd_orders(self, department_option):
        """Update orders based on department selection with LEFT JOIN."""
        if not self.dbConn:
            return "Database connection failed. Please check your connection settings."

        try:
            cursor = self.dbConn.cursor()
            
            # Define the update query with LEFT JOIN
            if department_option == "ALL DEPARTMENTS":
                query = """
                UPDATE orders_internal_orders o
                LEFT JOIN orders_departments d ON o.dept_id = d.dept_id
                SET o.hd_approved = 0
                WHERE o.hd_approved =1
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
                and department=%s
                """
                cursor.execute(query, (department_option,))
            
            # Commit the changes
            self.dbConn.commit()

            # Check how many rows were updated
            affected_rows = cursor.rowcount
            
            if affected_rows == 0:
                return f"No orders found for {department_option} to update."
            
            return f"{affected_rows} records updated successfully for {department_option}."
        
        except Error as e:
            return f"Error updating orders: {str(e)}"

    def fetch_name(self):
        """Fetch name of the Bot User from the database"""
        if not self.dbConn:
            return "Database connection failed. Please check your connection"
        
        try:
            cursor = self.dbConn.cursor()
            cursor.execute("SELECT first_name as Username FROM ja_db.hrm_employees where emp_id=476")
            result = cursor.fetchone()  # Fetch the first result
            if result:
                return result[0]  # Return the username (first column of the result)
            else:
                return "Username not found"
        except Error as e:
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

    def fetch_employee_details(self, emp_id):
        """Fetch employee details based on Employee ID."""
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

            """, (emp_id,))  # ✅ Fix: Parameters go here properly
            
            return cursor.fetchone()
        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            return None

 


