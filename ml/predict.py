import pandas as pd
import joblib
import os

MODEL_PATH = "ml/model.pkl"

def predict_marks(input_data):
    # 1. Check if the model file exists before trying to load it
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at '{MODEL_PATH}'")
        return None

    try:
        # Load the trained model
        model = joblib.load(MODEL_PATH)
        
        # Create DataFrame with the input data
        X = pd.DataFrame([input_data])
        
        # Make prediction
        prediction = model.predict(X)
        raw_val = float(prediction[0])
        return max(0.0, min(100.0, raw_val))

        
    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        return None

# Input data for prediction
student_data = {
    "study_hours": 7,
    "attendance": 88,
    "previous_marks": 78,
    "assignments": 8
}

# Run the prediction
predicted_marks = predict_marks(student_data)

if predicted_marks is not None:
    print(f"Input Features: {student_data}")
    print(f"Predicted Final Marks: {predicted_marks:.2f}")