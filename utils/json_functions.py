import os
import json

def load_json_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                connections = json.load(file)
                return connections
            
            except json.JSONDecodeError:
                return {} 