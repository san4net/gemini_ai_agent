import os

import google
from google.genai import types

GOOGLE_API_KEY = 'AQ.Ab8RN6Lud5xZ2-c_iGETQnz3ExvlX7hel3vo1MVBWtxLAAxIKw'

def configure_api_key():
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY


def retry_config():
    return types.HttpRetryOptions(
        attempts=5,  # Maximum retry attempts
        exp_base=7,  # Delay multiplier
        initial_delay=1,  # Initial delay before first retry (in seconds)
        http_status_codes=[429, 500, 503, 504]  # Retry on these HTTP errors
    )


