# save_manager.py — Handles writing and reading save files using pickle serialization.

import pickle
import os

class SaveManager:
    # Creates the save folder if it doesn't already exist (exist_ok prevents errors
    # if the folder is already there)
    def __init__(self, file_extension, save_folder):
        self.file_extension = file_extension
        self.save_folder = save_folder
        os.makedirs(save_folder, exist_ok=True)

    # Serializes data to a binary file using pickle; "wb" = write binary
    def save_data(self, data, name):
        with open(self.save_folder + "/" + name + self.file_extension, "wb") as data_file:
            pickle.dump(data, data_file)

    # Deserializes and returns data from a binary save file; "rb" = read binary
    def load_data(self, name):
        with open(self.save_folder + "/" + name + self.file_extension, "rb") as data_file:
            data = pickle.load(data_file)
            return data