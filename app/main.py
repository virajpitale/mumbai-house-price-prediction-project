from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import joblib
import pandas as pd
import json
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load JSON data for dropdown options
def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

age_options = load_json('static/json/unique_values_age.json')
locality_options = load_json('static/json/unique_values_locality.json')
region_options = load_json('static/json/unique_values_region.json')
status_options = load_json('static/json/unique_values_status.json')
type_options = load_json('static/json/unique_values_type.json')

# Load the scaler used during training
scaler = joblib.load('static/models/min_max_scaler.pkl')

# Load the best Regression model
best_model = joblib.load('static/models/decisiontree_regressor_regression_model.pkl')

# Load encoding maps
with open('static/models/encoding_maps/locality_encoding_map.pkl', 'rb') as f:
    locality_encoding_map = joblib.load(f)

with open('static/models/encoding_maps/region_encoding_map.pkl', 'rb') as f:
    region_encoding_map = joblib.load(f)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "age_options": age_options,
        "locality_options": locality_options,
        "region_options": region_options,
        "status_options": status_options,
        "type_options": type_options
    })

@app.get("/dropdown-options/")
def get_dropdown_options():
    return {
        "age_options": age_options,
        "locality_options": locality_options,
        "region_options": region_options,
        "status_options": status_options,
        "type_options": type_options
    }

@app.post("/predict/")
async def predict(
    request: Request,
    bhk: int = Form(...),
    area: float = Form(...),
    type_encoded: str = Form(...),
    status_encoded: str = Form(...),
    age_encoded: str = Form(...),
    locality: str = Form(...),
    region: str = Form(...)
):
    try:
        # Encode locality and region
        locality_encoded = locality_encoding_map.get(locality, locality_encoding_map.get('Other', 0))
        region_encoded = region_encoding_map.get(region, region_encoding_map.get('Other', 0))

        # Prepare input data
        input_data = {
            'bhk': bhk,
            'area': area,
            'locality_target_encoded': locality_encoded,
            'region_target_encoded': region_encoded,
            f'type_{type_encoded}': 1,
            f'status_{status_encoded}': 1,
            f'age_{age_encoded}': 1
        }

        # Create a DataFrame from input data
        input_df = pd.DataFrame([input_data])

        # Ensure dummy columns are present and aligned
        necessary_columns = [
            'bhk', 'area', 'locality_target_encoded', 'region_target_encoded',
            'type_Independent House', 'type_Penthouse', 'type_Studio Apartment', 'type_Villa',
            'status_Under Construction', 'age_Resale', 'age_Unknown'
        ]

        # Add missing columns with default value 0
        for col in necessary_columns:
            if col not in input_df.columns:
                input_df[col] = 0

        # Ensure columns are in the correct order
        input_df = input_df[necessary_columns]

        # Scale numerical features using the loaded MinMaxScaler
        input_df[['bhk', 'area']] = scaler.transform(input_df[['bhk', 'area']])

        # Make prediction using the best model Regression model
        predicted_price = best_model.predict(input_df)[0]

        # Convert predicted price to lakhs and round off to two decimal places
        predicted_price_lakhs = round(predicted_price / 100000, 2)

        # Return JSON response with predicted price in lakhs
        return JSONResponse(content={"predicted_price": predicted_price_lakhs})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


# Run the FastAPI server with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
