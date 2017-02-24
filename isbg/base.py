from enum import Enum

class ISBGError(Exception):
    pass

class ISBGImapError(ISBGError):
    def __init__(self, res, message):
        self.res = res
        self.message = message
