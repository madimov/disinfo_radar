import configparser

class Config:

    cfg = configparser.ConfigParser() # static class variables
    cfg.read('config.ini')