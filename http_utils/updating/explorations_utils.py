import json
from models.implicitALS.singleton import SharedModel


def load_explorations_model(path):
    mapper = SharedModel().mapper

    categories = json.load(open(path))
    # map data
    for cat in categories.keys():
        items = list(map(mapper.get_item_ix, categories[cat]))
        items = list(filter(lambda i: i != -1, items))  # filter unknown items
        categories[cat] = items
    return categories
