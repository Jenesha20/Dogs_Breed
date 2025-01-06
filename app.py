from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import certifi

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB client setup
client = MongoClient(
    "mongodb+srv://jeneshamalars:jene2011@cluster0.6xjwy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    tlsCAFile=certifi.where()
)
db = client['Dogs_Breed']
users = db['users']

# Define class names for predictions
verbose_name = {
    0: 'Afghan', 
    1: 'African Wild Dog',
    2: 'Airedale',
    3: 'American Hairless',
    4: 'American Spaniel',   
    5: 'Basenji',
    6: 'Basset',
    7: 'Beagle',
    8: 'Bearded Collie',   
    9: 'Bermaise',
    10: 'Bichon Frise',
    11: 'Blenheim',
    12: 'Bloodhound',   
    13: 'Bluetick',
    14: 'Border Collie',
    15: 'Borzoi',
    16: 'Boston Terrier',
    17: 'Boxer',
    18: 'Bull Mastiff',
    19: 'Bull Terrier',
    20: 'Bulldog',
    21: 'Cairn',
    22: 'Chihuahua',
    23: 'Chinese Crested',
    24: 'Chow',
    25: 'Clumber',
    26: 'Cockapoo',
    27: 'Cocker',
    28: 'Collie',
    29: 'Corgi',
    30: 'Coyote',
    31: 'Dalmation',
    32: 'Dhole',
    33: 'Dingo',
    34: 'Doberman',
    35: 'Elk Hound',
    36: 'French Bulldog',
    37: 'German Sheperd',
    38: 'Golden Retriever',
    39: 'Great Dane',
    40: 'Great Perenees',
    41: 'Greyhound',
    42: 'Groenendael',
    43: 'Irish Spaniel',
    44: 'Irish Wolfhound',
    45: 'Japanese Spaniel',
    46: 'Komondor',
    47: 'Labradoodle',
    48: 'Labrador',
    49: 'Lhasa',
    50: 'Malinois',
    51: 'Maltese',
    52: 'Mex Hairless',
    53: 'Newfoundland',
    54: 'Pekinese',
    55: 'Pit Bull',
    56: 'Pomeranian',
    57: 'Poodle',
    58: 'Pug',
    59: 'Rhodesian',
    60: 'Rottweiler',
    61: 'Saint Bernard',
    62: 'Schnauzer',
    63: 'Scotch Terrier',
    64: 'Shar_Pei',
    65: 'Shiba Inu',
    66: 'Shih-Tzu',
    67: 'Siberian Husky',
    68: 'Vizsla',
    69: 'Yorkie'
}

# Lazy model loading to save memory
model = None

def load_dog_breed_model():
    global model
    if model is None:
        dependencies = {'auc_roc': tf.keras.metrics.AUC}
        model = load_model('model/xception.h5', custom_objects=dependencies)
    return model

# Function to preprocess image and predict label
def predict_label(img_path):
    model = load_dog_breed_model()
    try:
        test_image = image.load_img(img_path, target_size=(224, 224))  # Resize to the model input size
        test_image = image.img_to_array(test_image) / 255.0  # Normalize the image
        test_image = np.expand_dims(test_image, axis=0)  # Reshape to fit model input

        predictions = model.predict(test_image)
        predicted_class = np.argmax(predictions, axis=1)[0]
        return verbose_name[predicted_class]
    except Exception as e:
        return f"Error in prediction: {str(e)}"

# Routes for user authentication
@app.route("/signup", methods=['POST'])
def signup():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if users.find_one({"email": email}):
        flash("Email already exists. Please log in.", "error")
        return redirect(url_for('login_page'))

    if password != confirm_password:
        flash("Passwords do not match.", "error")
        return redirect(url_for('login_page'))

    hashed_password = generate_password_hash(password)
    users.insert_one({
        "name" : name,
        "email": email,
        "password": hashed_password
    })    
    return redirect(url_for('register_success'))

@app.route("/login", methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = users.find_one({"email": email})

    if user and check_password_hash(user['password'], password):
        session['user_email'] = email
        session['user_name'] = user['name']
        return redirect(url_for('index'))
    else:
        flash("Invalid credentials. Please try again.", "error")
        return redirect(url_for('login_page'))

@app.route("/logout")
def logout():
    session.pop('user', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('first'))

# Routes for skin cancer prediction functionality

@app.route("/")
@app.route("/first")
def first():
    return render_template('first.html')

@app.route("/login_page")
def login_page():
    return render_template('login.html')

@app.route("/register_success")
def register_success():
    return render_template('register_success.html')

@app.route("/index", methods=['GET', 'POST'])

@app.route("/index", methods=['GET', 'POST'])
def index():
    if 'user_name' in session:
        return render_template("index.html", user_name=session['user_name'])
    else:
        return redirect(url_for('first'))

@app.route("/submit", methods=['POST'])
def get_output():
    if request.method == 'POST':
        if 'my_image' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        img = request.files['my_image']

        if img.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if img:
            # Save image to the static folder
            img_path = os.path.join('static/tests/', img.filename)
            img.save(img_path)
            print(img_path)

            # Get prediction
            prediction_result = predict_label(img_path)

            return render_template("prediction.html", prediction=prediction_result, img_path=img_path , user_name=session['user_name'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable if available
    app.run(debug=True, host='0.0.0.0', port=port)