import configparser

def read_config_file(path):
    config = configparser.ConfigParser()
    config.read(path)
    return config