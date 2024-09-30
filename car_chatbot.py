import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

# Initialize Firebase
cred = credentials.Certificate("car-listing-website-firebase-adminsdk-7mba9-19d0eb73af.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Process user input to extract preferences
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

    return preferences

# Query the Firestore database based on user preferences
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
        return cars, None

    except Exception as e:
        print(f"Error querying database: {e}")
        return None, f"I'm sorry, but there was an error processing your request. Please try again later."

# Filter cars based on price if provided
def filter_cars(cars, preferences):
    if 'price' in preferences:
        cars = [car for car in cars if float(car.get('price', 0)) <= float(preferences['price'])]
    return cars

# Format the car details for a readable response
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

# Home route
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Car Recommendation Chatbot API"}), 200

# Chat route to handle user queries
@app.route('/chat', methods=['POST'])
def chat():
    if not request.json or 'message' not in request.json:
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400

    user_input = request.json['message']
    
    # Extract preferences from user input
    preferences = process_user_input(user_input)
    
    # Query the database based on preferences
    cars, error_message = query_database(preferences)

    if error_message:
        return jsonify({"response": error_message}), 500

    if not cars:
        return jsonify({"response": "I'm sorry, I couldn't find any cars in our database. Please try a different query."}), 200

    # Filter cars based on price if applicable
    filtered_cars = filter_cars(cars, preferences)

    # Format the response
    if filtered_cars:
        response_message = f"I found {len(filtered_cars)} car(s) matching your preferences. Here are up to 2 options:"
        car_details = "\n".join([format_car(car) for car in filtered_cars[:2]])  # Limit to 2 results
    else:
        response_message = "I couldn't find any cars exactly matching your preferences, but here are up to 2 options:"
        car_details = "\n".join([format_car(car) for car in cars[:2]])  # Show up to 2 cars from the database

    return jsonify({'response': f"{response_message}\n{car_details}"}), 200

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
