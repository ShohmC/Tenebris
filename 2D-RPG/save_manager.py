import json
import os

class SaveManager:
    def __init__(self, save_dir=".save", data_dir="SaveData"):
        self.save_dir = save_dir
        self.data_dir = data_dir
        self.full_path = os.path.join(save_dir, data_dir)
        os.makedirs(self.full_path, exist_ok=True)

    def save_data(self, data, slot_name):
        """Save a dictionary as a JSON file inside the slot folder."""
        slot_folder = os.path.join(self.full_path, slot_name)
        os.makedirs(slot_folder, exist_ok=True)
        filepath = os.path.join(slot_folder, "save.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load_data(self, slot_name):
        """Load a dictionary from a JSON file."""
        filepath = os.path.join(self.full_path, slot_name, "save.json")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"No save file for slot '{slot_name}'")
        with open(filepath, "r") as f:
            return json.load(f)