import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate("car-listing-website-firebase-adminsdk-7mba9-19d0eb73af.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Function to process user input and extract preferences
def process_user_input(user_input):
    preferences = {}
    
    # Extract fuel type
    fuel_types = ['electric', 'gasoline', 'petrol', 'hybrid']
    for fuel in fuel_types:
        if fuel in user_input.lower():
            preferences['fuel'] = fuel
            break
    
    # Extract price
    price_match = re.search(r'\$?(\d+),?(\d+)?', user_input)
    if price_match:
        price = int(price_match.group(1) + (price_match.group(2) or ''))
        preferences['price'] = price
    
    # Extract brand
    brands = ['BMW', 'Mercedes-Benz', 'Toyota', 'Nissan', 'Lamborghini', 'Hyundai']
    for brand in brands:
        if brand.lower() in user_input.lower():
            preferences['brand'] = brand
            break
    
    # Extract car type
    car_types = ['SUV', 'Sedan', 'Truck', 'Convertible']
    for car_type in car_types:
        if car_type.lower() in user_input.lower():
            preferences['carType'] = car_type
            break
    
    # Extract color
    colors = ['black', 'white', 'red', 'blue', 'green', 'silver', 'gray']
    for color in colors:
        if color in user_input.lower():
            preferences['color'] = color
            break
    
    print(f"Debug: Extracted preferences: {preferences}")
    return preferences

# Function to query the database based on user preferences
def query_database(preferences):
    cars_ref = db.collection('cars')
    query = cars_ref

    if 'fuel' in preferences:
        query = query.where('fuel', '==', preferences['fuel'].capitalize())
    if 'brand' in preferences:
        query = query.where('brand', '==', preferences['brand'].capitalize())
    if 'carType' in preferences:
        query = query.where('carType', '==', preferences['carType'].capitalize())
    if 'color' in preferences:
        query = query.where('color', '==', preferences['color'].capitalize())
    
    try:
        # Fetch cars based on the filtered query
        results = query.get()
        cars = [doc.to_dict() for doc in results]
        
        print(f"Debug: Query preferences: {preferences}")
        print(f"Debug: Number of cars found: {len(cars)}")
        if cars:
            print(f"Debug: First car found: {cars[0]}")
        else:
            print("Debug: No cars found")
        return cars, None

    except Exception as e:
        print(f"Error querying database: {e}")
        return None, "I'm sorry, but there was an error processing your request. Please try again later."

# Function to filter cars based on price preference
def filter_cars(cars, preferences):
    filtered_cars = cars
    if 'price' in preferences:
        filtered_cars = [car for car in filtered_cars if float(car.get('price', 0)) <= float(preferences['price'])]
    return filtered_cars

# Function to format car details
def format_car(car):
    return f"""
{car.get('brand', 'N/A')} {car.get('name', 'N/A')}
Type: {car.get('carType', 'N/A')}
Color: {car.get('color', 'N/A')}
Interior Color: {car.get('interiorColor', 'N/A')}
Transmission: {car.get('transmission', 'N/A')}
Engine: {car.get('engine', 'N/A')}
Fuel: {car.get('fuel', 'N/A')}
Mileage: {car.get('mileage', 'N/A')}
Price: ${car.get('price', 'N/A')}
VIN: {car.get('VIN', 'N/A')}
Image: {car.get('image', 'N/A')}
"""

# Flask app setup
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Car Recommendation Chatbot API"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    if not request.json or 'message' not in request.json:
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400
    
    user_input = request.json['message']

    # Process user input to extract preferences
    preferences = process_user_input(user_input)

    # Query the database with the extracted preferences
    cars, error_message = query_database(preferences)

    if error_message:
        return jsonify({'response': error_message}), 200
    elif not cars:
        return jsonify({'response': "I'm sorry, I couldn't find any cars in our database. Please try a different query."}), 200

    # Filter cars based on price preference if available
    filtered_cars = filter_cars(cars, preferences)

    if filtered_cars:
        response = f"I found {len(filtered_cars)} car(s) matching your preferences. Here are up to 2 options:"
        for i, car in enumerate(filtered_cars[:2], 1):
            response += f"\n\n{i}. {format_car(car)}"
    else:
        response = "I couldn't find any cars exactly matching your preferences, but here are up to 2 options:"
        for i, car in enumerate(cars[:2], 1):
            response += f"\n\n{i}. {format_car(car)}"

    return jsonify({'response': response}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
