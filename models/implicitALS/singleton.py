class ModelSingleton(object):
    # https://stackoverflow.com/a/6798042
    _instances = {}

    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(ModelSingleton, class_).__new__(class_, *args, **kwargs)
        return class_._instances[class_]


class SharedModel(ModelSingleton):
    shared_model = None
    mapper = None # mappers realID <-> innerID updates with new data such as models
