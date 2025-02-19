import requests
import logging
from config import CO2_API_URL, BUILDING_ID, HEADERS

# Fetch CO2 Sensor Data
def fetch_room_data(building_id="512"):
    url = "https://co2.mesh.lv/api/device/list"  # Correct API endpoint
    payload = {
        "buildingId": building_id,
        "captchaToken": None
    }

    headers = {
        'Content-Type': 'application/json',  # Ensure correct content type
        'Accept': 'application/json',  # Accept JSON response
        'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',  # Optional: user-agent to match browser
    }

    # Make a POST request with the payload and headers
    response = requests.post(url, json=payload, headers=headers)

    logging.info(f"Response Status Code: {response.status_code}")  # Log status code

    # Check if the request was successful and attempt to parse JSON
    if response.status_code == 200:
        try:
            return response.json()  # Try to parse as JSON
        except ValueError as e:
            logging.error(f"JSON decoding error: {e}")
            return []  # Return empty list if JSON parsing fails
    else:
        logging.error(f"Request failed with status code {response.status_code}")
        return []  # Return empty list if the request failed