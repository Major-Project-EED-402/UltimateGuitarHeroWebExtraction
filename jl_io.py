import pickle

def load_to_file(data, path):
    with open(path, "wb") as file:
        pickle.dump(data, file)

def read_from_file(path):
    with open(path, "rb") as file:
        return pickle.load(file)