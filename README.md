Food Delivery Time Prediction
Overview
A full-stack machine learning project that predicts food delivery times in real time.
The system includes a complete two-portal web application — one for customers and one
for delivery drivers — built on top of a CatBoost regression model trained on real-world
delivery data.
Demo
▶️ Watch Demo Video

Web Application Features
👤 User Portal

Place a food order
Track order status in real time (Processing → Picked up → Out for delivery)
View predicted delivery time
Rate the driver after delivery

🚗 Driver Portal

Accept or reject incoming orders
Update order status at each stage (Preparing → Picked up → Ready to deliver)
Input real-time conditions (weather, road traffic) for accurate prediction
View delivery details


Project Structure
food-delivery-time-prediction/
├── project.ipynb                        # Full ML pipeline (EDA → model training)
├── catboost_delivery_time_model.pkl     # Saved CatBoost model
└── webapp/                              # Flask web application

ML Pipeline (inside notebook)

Data loading and understanding
Exploratory Data Analysis (EDA)
Data cleaning and feature engineering
Model comparison (Linear Regression, Decision Tree, Random Forest, XGBoost, CatBoost)
Hyperparameter tuning
Model saving for deployment


Tools & Technologies
CategoryToolsLanguagePythonData ProcessingPandas, NumPyVisualisationMatplotlib, SeabornMachine LearningScikit-learn, XGBoost, CatBoostWeb FrameworkFlaskOtherGeopy (distance calculation), Joblib (model saving)

How to Run the Web App

Navigate to the webapp/ folder

   cd webapp

Install dependencies

   pip install -r requirements.txt

Run the app

   python app.py

Open your browser at http://localhost:5000


Dataset
The dataset contains real-world food delivery records with the following key features:

Delivery person age and ratings
Restaurant and delivery location (latitude/longitude)
Weather conditions and road traffic density
Vehicle type and condition
Order type and festival indicator
Target variable: Delivery time in minutes
