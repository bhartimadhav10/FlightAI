import gradio as gr
import json
import pandas as pd
from datetime import datetime
import os
import requests

# Function to load JSON data from a file
def load_json(file_path):
    if os.path.exists(file_path):
        print(f"File found: {file_path}")  # Debugging statement
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file: {file_path}")  # Debugging statement
            return []  # Return empty list if JSON is invalid
    else:
        print(f"File does not exist: {file_path}")  # Debugging statement
        return []  # Return empty list if file does not exist
# Function to save JSON data to a file
def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Function to search flights
def search_flights(source=None, destination=None, date=None, passenger_count=1, airline=None):
    flights = load_json("flights.json")
    print("Loaded Flights Data:", flights)  # Debugging statement

    results = []
    
    for flight in flights:
        # Check source
        if source and flight["source"].lower() != source.lower():
            continue
        # Check destination
        if destination and flight["destination"].lower() != destination.lower():
            continue
        # Check date
        if date:
            try:
                if datetime.strptime(flight["date"], "%Y-%m-%d").date() != datetime.strptime(date, "%Y-%m-%d").date():
                    continue
            except ValueError:
                print(f"Invalid date format for flight: {flight['date']}")
                continue
        # Check passenger count
        if flight["seats"] < int(passenger_count):
            continue
        # Check airline
        if airline and flight["airline"].lower() != airline.lower():
            continue
        
        results.append(flight)
    
    # Return a DataFrame if flights are found, else return an empty DataFrame
    if results:
        df = pd.DataFrame(results)
        print("Search Results DataFrame:", df)  # Debugging statement
        return df
    else:
        empty_df = pd.DataFrame(columns=["id", "source", "destination", "date", "seats", "airline"])  # Return an empty DataFrame with the same columns
        print("No flights found, returning empty DataFrame.")  # Debugging statement
        return empty_df

# Function to book a flight
def book_flight(flight_id, name, email, passenger_count):
    flights = load_json("flights.json")
    bookings = load_json("bookings.json")
    
    if not flights or not bookings:
        return "Error loading flight or booking data."

    # Debugging statement
    print("Loaded Flights Data:", flights)
    print("Loaded Bookings Data:", bookings)

    for flight in flights:
        if flight["id"] == flight_id:
            if flight["seats"] >= int(passenger_count):
                flight["seats"] -= int(passenger_count)
                
                booking = {
                    "id": len(bookings) + 1,
                    "flight_id": flight_id,
                    "name": name,
                    "email": email,
                    "passenger_count": passenger_count,
                    "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                bookings.append(booking)
                
                save_json("flights.json", flights)
                save_json("bookings.json", bookings)
                
                return f"Booking successful! Your booking ID is {booking['id']}"
            else:
                return "Booking failed. Not enough seats available."
    
    return "Booking failed. Flight ID not found."

# Function to view bookings
def view_bookings(email):
    bookings = load_json("bookings.json")
    
    if not bookings:
        return "Error loading booking data."
    
    # Debugging statement
    print("Loaded Bookings Data:", bookings)

    results = [b for b in bookings if b.get("email") == email]
    
    if results:
        df = pd.DataFrame(results)
        print("View Bookings DataFrame:", df)  # Debugging statement
        return df
    else:
        empty_df = pd.DataFrame(columns=["id", "flight_id", "name", "email", "passenger_count", "booking_date"])  # Return an empty DataFrame with the same columns
        print("No bookings found for this email, returning empty DataFrame.")  # Debugging statement
        return empty_df

# Flight assistant function
def flight_assistant(messages, conversation_history=None):
    if conversation_history is None:
        conversation_history = []
    
    if isinstance(messages, list):
        if len(messages) > 0 and isinstance(messages[-1], dict):
            user_message = messages[-1].get("content", "").lower()
        else:
            return [{"role": "assistant", "content": "Error: Last message in list is not in expected format."}]
    elif isinstance(messages, str):
        user_message = messages.lower()
    else:
        return [{"role": "assistant", "content": "Error: Invalid message format."}]
    
    conversation_history.append({"role": "user", "content": user_message})
    
    # Define Ollama API URL (Local setup)
    ollama_url = "http://localhost:11434/v1/chat/completions"
    
    payload = {
        "model": "llama3.2:latest",
        "messages": conversation_history
    }
    
    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(ollama_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        assistant_reply = data["choices"][0]["message"]["content"]
        conversation_history.append({"role": "assistant", "content": assistant_reply})
        
        # Handle flight queries
        if "flights on" in user_message or "list flights" in user_message:
            if "from" in user_message and "to" in user_message:
                source = user_message.split("from")[-1].split("to")[0].strip()
                destination = user_message.split("to")[-1].strip()
                
                date = None
                if "on" in user_message:
                    date = user_message.split("on")[-1].strip()
                
                flights = load_json("flights.json")
                filtered_flights = []
                
                for flight in flights:
                    if flight["source"].lower() == source.lower() and flight["destination"].lower() == destination.lower():
                        if date:
                            if datetime.strptime(flight["date"], "%Y-%m-%d").date() == datetime.strptime(date, "%Y-%m-%d").date():
                                filtered_flights.append(flight)
                        else:
                            filtered_flights.append(flight)
                
                if filtered_flights:
                    flight_details = [f"Flight ID: {f['id']}, Airline: {f['airline']}, Date: {f['date']}, Seats: {f['seats']}" for f in filtered_flights]
                    assistant_reply = "\n".join(flight_details)
                else:
                    assistant_reply = "No flights found matching your query."
        
        # Handle booking cancellation
        elif "cancel booking" in user_message:
            try:
                booking_id = int(user_message.split("booking id")[-1].strip())
                email = user_message.split("email is")[-1].strip()
                
                bookings = load_json("bookings.json")
                updated_bookings = [b for b in bookings if not (b["id"] == booking_id and b["email"] == email)]
                
                if len(updated_bookings) != len(bookings):
                    save_json("bookings.json", updated_bookings)
                    assistant_reply = f"Booking {booking_id} has been successfully canceled."
                else:
                    assistant_reply = "Booking ID not found or email mismatch."

            except ValueError:
                assistant_reply = "Error: Please provide a valid booking ID."

        # Handle updating passenger count
        elif "update passengers" in user_message:
            try:
                booking_id = int(user_message.split("booking id")[-1].strip())
                email = user_message.split("email is")[-1].strip()
                new_passenger_count = int(user_message.split("to")[-1].strip())
                
                bookings = load_json("bookings.json")
                for booking in bookings:
                    if booking["id"] == booking_id and booking["email"] == email:
                        booking["passenger_count"] = new_passenger_count
                        save_json("bookings.json", bookings)
                        assistant_reply = f"Booking {booking_id} passenger count has been updated to {new_passenger_count}."
                        break
                else:
                    assistant_reply = "Booking ID not found or email mismatch."

            except ValueError:
                assistant_reply = "Error: Please provide valid booking ID and new passenger count."

        conversation_history.append({"role": "assistant", "content": assistant_reply})

        return [{"role": "assistant", "content": assistant_reply, "conversation": conversation_history}]
    
    except requests.exceptions.RequestException as e:
        return [{"role": "assistant", "content": f"Error: Unable to connect to Ollama API. {str(e)}"}]

# Gradio UI
def main():
    with gr.Blocks() as demo:
        gr.Markdown("# FlightAI - Flight Search & Booking System")
        
        with gr.Tab("Flight Assistant AI (Chatbot)"):
            chatbot = gr.Chatbot(type='messages')
            msg = gr.Textbox(placeholder="Ask me anything about flights...", show_label=False)
            submit_btn = gr.Button("Submit")
            
            submit_btn.click(flight_assistant, inputs=msg, outputs=chatbot)
        
        with gr.Tab("Search Flights"):
            source = gr.Textbox(label="Source")
            destination = gr.Textbox(label="Destination")
            date = gr.Textbox(label="Date (YYYY-MM-DD)")
            passenger_count = gr.Number(label="Passengers", value=1)
            airline = gr.Textbox(label="Preferred Airline (Optional)")
            search_btn = gr.Button("Search Flights")
            result = gr.Dataframe()
            
            search_btn.click(search_flights, inputs=[source, destination, date, passenger_count, airline], outputs=result)
        
        with gr.Tab("Book Flight"):
            flight_id = gr.Number(label="Flight ID")
            name = gr.Textbox(label="Full Name")
            email = gr.Textbox(label="Email")
            passenger_count = gr.Number(label="Passengers", value=1)
            book_btn = gr.Button("Book Flight")
            booking_status = gr.Textbox()
            
            book_btn.click(book_flight, inputs=[flight_id, name, email, passenger_count], outputs=booking_status)
        
        with gr.Tab("View Bookings"):
            email_lookup = gr.Textbox(label="Enter Email")
            view_btn = gr.Button("View Bookings")
            bookings_output = gr.Dataframe()
            
            view_btn.click(view_bookings, inputs=email_lookup, outputs=bookings_output)
        
    demo.launch()

if __name__ == "__main__":
    main()