from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import requests
import json
from flask_mailman import Mail, EmailMessage

app = Flask(__name__)

# Load the trained model
model = joblib.load("crop_model.pkl")

# Load feature names (ensures correct input format)
with open("feature_names.json", "r") as f:
    feature_names = json.load(f)

# OpenWeather API (Replace with your API key)
WEATHER_API_KEY = "233a169eca4c3d30d93928de0883ee9a"

# Email Configuration (Replace with your credentials)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "ashwinnandacool@gmail.com"
app.config["MAIL_PASSWORD"] = "zotv xwkm fmzy woli"
app.config["MAIL_DEFAULT_SENDER"] = "ashwinnandacool@gmail.com"

mail = Mail(app)
mail.init_app(app)

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
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route("/predict_crop", methods=["POST"])
def predict_crop():
    try:
        data = request.json
        city = data.get("city")

        # Fetch temperature & humidity automatically
        temperature, humidity = get_weather(city)

        if temperature is None or humidity is None:
            return jsonify({"error": "Could not fetch weather data for the given city"}), 400

        # Extract other inputs
        N = float(data.get("nitrogen"))
        P = float(data.get("phosphorus"))
        K = float(data.get("potassium"))
        ph = float(data.get("ph"))
        rainfall = float(data.get("rainfall"))

        # Create DataFrame with correct feature names
        new_data = pd.DataFrame([[N, P, K, temperature, humidity, ph, rainfall]], columns=feature_names)
       
        predicted_crop = model.predict(new_data)[0]

        return jsonify({"suggested_crop": predicted_crop})
    
    except Exception as e:
       return jsonify({"error": str(e)}), 500

@app.route("/send_mail", methods=["POST"])
def send_mail():
    try:
        name = request.form["name"]
        recipient_email = request.form["email"]
        subject = request.form["subject"]
        message = request.form["message"]

        # Construct email body
        body = f"Name: {name}\n\nMessage:\n{message}"

        # Send email using Flask-Mailman
        email = EmailMessage(subject, body, to=[recipient_email])
        email.send()

        return "Email sent successfully!"
    
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
   app.run(debug=True)
