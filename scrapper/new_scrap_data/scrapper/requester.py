import asyncio
import logging
import threading
import concurrent.futures
from time import sleep
from enum import Enum

__all__ = ['concurrent_load']


class DownloadState(Enum):
    OK = 1
    ERROR = 2


def load_users(sessions, urls):
    # Entry point. Loads batch of users from site using given session

    # Creating tasks
    threads = [DownloadThread(session, url) for session, url in zip(sessions, urls)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    data = [(t.result, t.state) for t in threads]
    return data



class DownloadThread(threading.Thread):
    def __init__(self, session, url):
        self.session = session
        self.url = url
        self.result = None
        self.state = None
        threading.Thread.__init__(self)

    def load_page(self):
        state = DownloadState.OK
        try:
            res = self.session.load_user(self.url)
        except Exception as e:
            state = DownloadState.ERROR
            logging.error("Unexpected", e, "accured on url" % self.url)
        self.result = res.text
        self.state = state
#         print("loaded url %s" % self.url)

    def run(self):
#         print("loading url %s" % self.url)
        self.load_page()