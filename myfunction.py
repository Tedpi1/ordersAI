



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


