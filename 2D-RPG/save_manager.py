import pickle
import os

class SaveManager:
    def __init__(self, file_extension, save_folder):
        self.file_extension = file_extension
        self.save_folder = save_folder
        os.makedirs(save_folder, exist_ok=True)

    def save_data(self, data, name):
        with open(self.save_folder + "/" + name + self.file_extension, "wb") as data_file:
            pickle.dump(data, data_file)

    def load_data(self, name):
        with open(self.save_folder + "/" + name + self.file_extension, "rb") as data_file:
            data = pickle.load(data_file)
            return data