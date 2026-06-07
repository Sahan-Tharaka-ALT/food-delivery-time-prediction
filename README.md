# Food Delivery Time Prediction

## Overview
A full-stack machine learning project that predicts food delivery times in real time.
The system includes a complete two-portal web application — one for customers and one
for delivery drivers — built on top of a CatBoost regression model trained on real-world
delivery data.

## Demo
▶️ [Watch Demo Video](https://drive.google.com/file/d/1g5FCzPTl_Ac_hq9udVowsm_TfO2bJ3dk/view?usp=sharing)

---

## Web Application Features

### 👤 User Portal
- Place a food order
- Track order status in real time (Processing → Picked up → Out for delivery)
- View predicted delivery time
- Rate the driver after delivery

### 🚗 Driver Portal
- Accept or reject incoming orders
- Update order status at each stage (Preparing → Picked up → Ready to deliver)
- Input real-time conditions (weather, road traffic) for accurate prediction
- View delivery details

---

## Project Structure

---

## ML Pipeline (inside notebook)
1. Data loading and understanding
2. Exploratory Data Analysis (EDA)
3. Data cleaning and feature engineering
4. Model comparison (Linear Regression, Decision Tree, Random Forest, XGBoost, CatBoost)
5. Hyperparameter tuning
6. Model saving for deployment

---

## Tools & Technologies
| Category | Tools |
|---|---|
| Language | Python |
| Data Processing | Pandas, NumPy |
| Visualisation | Matplotlib, Seaborn |
| Machine Learning | Scikit-learn, XGBoost, CatBoost |
| Web Framework | Flask |
| Other | Geopy (distance calculation), Joblib (model saving) |

---

## How to Run the Web App
1. Navigate to the `webapp/` folder
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python app.py`
4. Open your browser at `http://localhost:5000`

---

## Dataset
The dataset contains real-world food delivery records with the following key features:
- Delivery person age and ratings
- Restaurant and delivery location (latitude/longitude)
- Weather conditions and road traffic density
- Vehicle type and condition
- Order type and festival indicator
- Target variable: Delivery time in minutes
