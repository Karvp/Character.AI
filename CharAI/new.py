__all__ = ['File', 'Post', 'Character']

from io import BytesIO
from os.path import basename

class File:
    def __init__(self, file: str|BytesIO, *, content_type: str = None, name: str = None):
        self.name = name
        self.content_type = content_type
        if type(file) == str:
            self.file = open(file, 'rb')
            if name == None or len(name) == 0:
                self.name = basename(self.file.name)
        elif isinstance(file, BytesIO):
            self.file = file
            self.name = name
        else:
            raise TypeError("'file' object must be string or BytesIO")
    def extract(self):
        return self.name, self.file, self.content_type

from base64 import b64decode

class MP3:
    """ MP3 audio file content """

    def __init__(self, base64: str):
        self.data = b64decode(base64.encode("utf-8"))

    def dump(self, fp):
        fp.write(self.data)
    
    def binaries(self):
        return self.data
    

class Post:
    def __init__(self, title: str, text: str = "", image: File = None, options: dict = dict()):
        self.title = title
        self.text = text
        self.image = image
        self.options = options
        
class Character:
    pass
