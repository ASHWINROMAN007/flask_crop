from flask import Flask, jsonify, render_template, flash , redirect, request
import joblib
import pandas as pd
import requests
import json
import threading
from flask_mail import Mail, Message
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the trained model
model = joblib.load("crop_model.pkl")

# Load feature names (ensures correct input format)
with open("feature_names.json", "r") as f:
    feature_names = json.load(f)

# OpenWeather API (Replace with your API key)
WEATHER_API_KEY = "233a169eca4c3d30d93928de0883ee9a"

app.secret_key = 'your_secret_key'

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ecocropx2025@gmail.com'
app.config['MAIL_PASSWORD'] = 'jtif pkqr hwjb ryrr'
app.config['MAIL_DEFAULT_SENDER'] = 'ecocropx2025@gmail.com'

mail = Mail(app)

def get_weather(city):
    """Fetch temperature and humidity for a given city using OpenWeather API."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        return temperature, humidity
    else:
        return None, None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    try:
        data = request.json
        print("Received data:", data)  # Debug log
        
        # Validate input data
        required_fields = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
            
        # Extract all inputs directly from the request
        N = float(data.get("nitrogen"))
        P = float(data.get("phosphorus"))
        K = float(data.get("potassium"))
        temperature = float(data.get("temperature"))
        humidity = float(data.get("humidity"))
        ph = float(data.get("ph"))
        rainfall = float(data.get("rainfall"))

        print("Processed values:", {
            "N": N, "P": P, "K": K,
            "temperature": temperature,
            "humidity": humidity,
            "ph": ph,
            "rainfall": rainfall
        })  # Debug log

        # Create DataFrame with correct feature names
        new_data = pd.DataFrame([[N, P, K, temperature, humidity, ph, rainfall]], columns=feature_names)
       
        # Get probability predictions for all classes
        probabilities = model.predict_proba(new_data)[0]
        
        # Get indices of top 3 predictions
        top_3_indices = probabilities.argsort()[-3:][::-1]
        
        # Get the crop names and their probabilities
        top_3_crops = []
        for idx in top_3_indices:
            crop_name = model.classes_[idx]
            probability = probabilities[idx] * 100  # Convert to percentage
            top_3_crops.append({
                "crop": crop_name,
                "probability": round(probability, 2)
            })

        print("Top 3 predicted crops:", top_3_crops)  # Debug log
        return jsonify({"recommendations": top_3_crops})
    
    except ValueError as ve:
        print("Value Error:", str(ve))  # Debug log
        return jsonify({"error": "Invalid input values. Please check your input data."}), 400
    except Exception as e:
        print("Error occurred:", str(e))  # Debug log
        print("Error type:", type(e).__name__)  # Debug log
        import traceback
        print("Traceback:", traceback.format_exc())  # Debug log
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

@app.route("/send-mail", methods=["POST"])
def sendMail():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    if not name or not subject or not message or not email:
        flash('All fields are required!', 'error')
        return redirect('/contact')

    msg = Message(
        subject=f"New Message from {name}",
        sender=email,
        recipients=[app.config['MAIL_USERNAME']],
        body=f"Name: {name}\nEmail: {email}\nSubject: {subject}\nMessage:\n{message}"
    )

    try:
        # Send email in a separate thread
        thread = threading.Thread(target=send_async_email, args=(app, msg))
        thread.start()
        flash('Email is being sent in the background!', 'success')
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'error')

    return redirect('/contact')

if __name__ == "__main__":
   app.run(debug=True)
