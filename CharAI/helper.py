

__all__ = ['FileUploader', 'dump', 'STYLE', 'randomKey', 'Sorted', 'ensure_sorted']

class DiffMapper:
    def __init__(self):
        self.status = {
            'created': 'created',
            'updated': 'updated',
            'deleted': 'deleted',
            'unchanged': 'unchanged'
        }

    def diff(self, obj1, obj2):
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            return self.diff_dict(obj1, obj2)
        elif isinstance(obj1, list) and isinstance(obj2, list):
            return self.diff_list(obj1, obj2)
        elif isinstance(obj1, set) and isinstance(obj2, set):
            return self.diff_set(obj1, obj2)
        elif isinstance(obj1, tuple) and isinstance(obj2, tuple):
            return self.diff_tuple(obj1, obj2)
        elif isinstance(obj1, str) and isinstance(obj2, str):
            return self.diff_primitive(obj1, obj2)
        elif isinstance(obj1, (int, float)) and isinstance(obj2, (int, float)):
            return self.diff_primitive(obj1, obj2)
        elif obj1 is None or obj2 is None:
            return self.diff_primitive(obj1, obj2)
        elif hasattr(obj1, '__dict__') and hasattr(obj2, '__dict__'):
            return self.diff_object(obj1, obj2)
        else:
            return self.diff_primitive(obj1, obj2)

    def diff_dict(self, dict1, dict2):
        diff = {}
        for key in dict1.keys():
            if key in dict2:
                diff[key] = self.diff(dict1[key], dict2[key])
            else:
                diff[key] = self.diff(dict1[key], None)

        for key in dict2.keys():
            if key not in dict1:
                diff[key] = self.diff(None, dict2[key])

        return diff

    def diff_list(self, list1, list2):
        diff = []
        min_len = min(len(list1), len(list2))
        for i in range(min_len):
            diff.append(self.diff(list1[i], list2[i]))

        if len(list1) > min_len:
            for i in range(min_len, len(list1)):
                diff.append(self.diff(list1[i], None))
        elif len(list2) > min_len:
            for i in range(min_len, len(list2)):
                diff.append(self.diff(None, list2[i]))

        return diff

    def diff_set(self, set1, set2):
        return {
            'type': self.compare(set1, set2),
            'data': set1 if set1 is not None else set2
        }

    def diff_tuple(self, tuple1, tuple2):
        diff = []
        min_len = min(len(tuple1), len(tuple2))
        for i in range(min_len):
            diff.append(self.diff(tuple1[i], tuple2[i]))

        if len(tuple1) > min_len:
            for i in range(min_len, len(tuple1)):
                diff.append(self.diff(tuple1[i], None))
        elif len(tuple2) > min_len:
            for i in range(min_len, len(tuple2)):
                diff.append(self.diff(None, tuple2[i]))

        return tuple(diff)

    def diff_primitive(self, value1, value2):
        return {
            'type': self.compare(value1, value2),
            'data': value1 if value1 is not None else value2
        }

    def diff_object(self, obj1, obj2):
        return self.diff(obj1.__dict__, obj2.__dict__)

    def compare(self, value1, value2):
        if value1 == value2:
            return self.status['unchanged']
        elif value1 is None:
            return self.status['created']
        elif value2 is None:
            return self.status['deleted']
        else:
            return self.status['updated']



from typing import Callable, Any

class DictWrapper(dict):
    def __init__(self, default: Any = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__default = default
    def __getitem__(self, __name: str) -> Any:
        return self.data.get(__name, self.__default)
    def pop(self, __name: str):
        return self.data.pop(__name, self.__default)
    def get(self, __name: str):
        return self.data.get(__name, self.__default)


from collections.abc import Collection

class __State(Collection):
    pass

class Sorted(__State):
    def __init__(self, i: Collection, key: Callable[[Any], Any] = lambda x: x):
        self.__dict__['__container__'] = i
        self.__dict__['__key__'] = key
        self.__dict__['ensure_sorted']()
            
    def ensure_sorted(self):
        def set(obj, key, value):
            obj.__dict__[key] = value
        def get(obj, key):
            return obj.__dict__[key]
        
        it = iter(get(self, '__container__'))
        key = get(self, '__key__')
        try:
            prev = next(it)
        except StopIteration:
            return
        check = True
        while check:
            try:
                this = next(it)
            except StopIteration:
                break
            check = key(prev) < key(this)
            prev = this
        if not check:
            set(self, '__container__', sorted(self.__container__, key=key))

    def __iter__(self):
        return iter(self.__container__)

    def __contains__(self, x: Any) -> bool:
        return x in self.__container__

    def __len__(self) -> int:
        return len(self.__container__)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.__container__, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self.__container__, name):
            setattr(self.__container__, name, value)
        else:
            self.__dict__[name] = value


    


class STYLE:
   class color:
       PURPLE = '\033[95m'
       CYAN = '\033[96m'
       DARKCYAN = '\033[36m'
       BLUE = '\033[94m'
       GREEN = '\033[92m'
       YELLOW = '\033[93m'
       RED = '\033[91m'
       MAGENTA = '\033[45m'
       BLACK = '\033[40m'
   class text:
       BOLD = '\033[1m'
       ITALIC = "\x1B[3m"
       UNDERSCORE = '\033[4m'
       BLINK = '\033[5m'
       REVERSE_VIDEO = '\033[7m'
       CONCEAL = '\033[8m'
   END = '\033[0m'

import json

def dump(res, *, indent: int = 4, default = str):
    print(json.dumps(res, indent=indent, default=default))
    
import tls_client, random, string
from CharAI.new import File


def randSeq(length: int, chars: str, encode: str = 'ascii'):
    return bytes().join(random.choice(chars).encode(encode) for _ in range(length))


class FileUploader:
    def __init__(self, sess: tls_client.Session):
        self.new_session(sess)
    def new_session(self, sess: tls_client.Session):
        self.sess = sess
        self.reset()
    def reset(self):
        self.__new_boundary()
        self.body = b''
    def __new_boundary(self):
        self.boundary = b"----WebKitFormBoundary" + randSeq(16, string.ascii_lowercase + string.ascii_uppercase + string.digits)
    def __generate_file_header(self, name: str, filename: str = None, content_type: str = None):
        header = b'Content-Disposition: form-data; name="' + name.encode() + b'"; '
        if filename != None:
            header += b'filename="' + filename.encode() + b'"; '
        if content_type != None:
            header += b'\r\nContent-Type: ' + content_type.encode()
        return header
    def addFile(self, name: str, file: File):
        filename, fp, mime = file.extract()

        self.body = b'--' + self.boundary + b'\r\n'
        self.body += self.__generate_file_header(name, filename, mime)
        self.body += b'\r\n\r\n'
        self.body += fp.read()
        self.body += b'\r\n--' + self.boundary + b'--\r\n'
    def upload(self, url: str, *, files = None, data = None, json = None, **kwargs):
        headers = kwargs.pop('headers', dict())
        headers['Content-Type'] = 'multipart/form-data; boundary=' + self.boundary.decode()
        return self.sess.post(url, data=self.body, headers=headers, **kwargs)
    
    
