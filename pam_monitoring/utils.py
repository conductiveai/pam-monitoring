import sys
import grpc
from prometheus_client import start_http_server

def get_size(obj):
    # If the object has a length, return it
    if isinstance(obj, (bytes, bytearray)):
        return len(obj)
    elif isinstance(obj, str):
        return len(obj.encode('utf-8'))
    elif isinstance(obj, (list, tuple)):
        return sum(get_size(item) for item in obj)
    elif isinstance(obj, dict):
        return sum(get_size(key) + get_size(value) for key, value in obj.items())
    else:
        # This is a fallback and may not be accurate for all types
        return sys.getsizeof(obj)
    
def GetStatusFromCode(code):
    for status in grpc.StatusCode:
        if status.value[0] == code:
            return status
    return None

def Start(port=8000):
    start_http_server(port)