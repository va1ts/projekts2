import requests
import time
import logging

# Cache data and timestamp
_cached_room_data = None
_last_fetch = 0
_CACHE_DURATION = 10  # seconds

def fetch_room_data_cached(building_id="512"):
    global _cached_room_data, _last_fetch
    current_time = time.time()
    if _cached_room_data is None or (current_time - _last_fetch) > _CACHE_DURATION:
        url = "https://co2.mesh.lv/api/device/list"
        payload = {
            "buildingId": building_id,
            "captchaToken": None
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        }
        response = requests.post(url, json=payload, headers=headers)
        logging.info(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                _cached_room_data = response.json()
            except ValueError as e:
                logging.error(f"JSON decoding error: {e}")
                _cached_room_data = []
        else:
            logging.error(f"Request failed with status code {response.status_code}")
            _cached_room_data = []
        _last_fetch = current_time
    return _cached_room_data
