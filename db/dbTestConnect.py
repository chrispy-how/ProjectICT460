import sqlite3

database_file = "chinook.db"
try:
    conn = sqlite3.connect(database_file)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM employees")

    employees_data = cursor.fetchall()

    if employees_data is not None:
        if employees_data:  # Check if the list is not empty
            print("Employee Records:")
            for employee in employees_data:
                print(f"{employee[0]} {employee[1]}, {employee[2]}: {employee[3]}")

        else:
            print("The 'employees' table exists but has no records.")
    else:
        print("Could not retrieve employee data.")          
    conn.close()  # Close the connection
except sqlite3.Error as e:
    print(f"An error occurred: {e}")
