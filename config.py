# config.py
from configparser import ConfigParser
from singleton import Singleton


class RTGOBConfig(metaclass=Singleton):
    def __init__(self):
        self.config = ConfigParser()
        self.config.read("config.ini")

        self.telegram = None
        self.ntfy = None

    def __getitem__(self, item):
        if item in self.config:
            return self.config[item]
        return None

    @property
    def has_telegram(self):
        if not self.telegram:
            self.telegram = (
                self["telegram"]
                and self["telegram"]["token"]
                and self["telegram"]["chat_id"]
                and len(self["telegram"]["token"].strip()) > 0
                and len(self["telegram"]["chat_id"].strip()) > 0
            )
        return self.telegram

    @property
    def has_ntfy(self):
        if not self.ntfy:
            self.ntfy = (
                self["ntfy"]
                and self["ntfy"]["server"]
                and self["ntfy"]["topic"]
                and len(self["ntfy"]["server"].strip()) > 0
                and len(self["ntfy"]["topic"].strip()) > 0
            )
        return self.ntfy
