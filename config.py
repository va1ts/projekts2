import logging

# Flask secret key
SECRET_KEY = 'your_secret_key'

# Logging configuration
logging.basicConfig(level=logging.DEBUG)


# API Config
CO2_API_URL = "https://co2.mesh.lv/api/device/list"
BUILDING_ID = "512"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}
