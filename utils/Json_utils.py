import json

def read_json(filename):
    with open(filename, 'r', encoding="utf8") as f:
        return json.load(f)
    
def save_json(filename, data):
    with open(filename, 'w', encoding="utf8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)