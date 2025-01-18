import json
from datetime import datetime
import os


# Function to load JSON data from a file
def load_json(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        # If the file doesn't exist or is empty, return an empty list
        return []


# Function to save JSON data to a file
def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Function to add a flight (Admin only)
def add_flight():
    # Admin input
    source = input("Enter source: ")
    destination = input("Enter destination: ")
    date = input("Enter flight date (YYYY-MM-DD): ")
    seats = input("Enter number of available seats: ")
    airline = input("Enter airline: ")
    
    # Load existing flights
    flights = load_json("flights.json")
    flight_id = len(flights) + 1  # Generate new flight ID
    
    # Create new flight entry
    flight = {
        "id": flight_id,
        "source": source,
        "destination": destination,
        "date": date,
        "seats": int(seats),
        "airline": airline
    }
    
    # Add new flight to the list and save it
    flights.append(flight)
    save_json("flights.json", flights)
    
    print(f"Flight added successfully with ID {flight_id}")

# Run the script only if it's executed directly (not imported)
if __name__ == "__main__":
    add_flight()
