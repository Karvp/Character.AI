# Character.AI
An unofficial high level API for character.ai for Python

# Introduction
The original idea was from [kramcat's CharacterAI](https://github.com/kramcat/characterai). This library aims on ease of use rather than a more functional library.

> [!NOTE]
> This library is developing. Every contribution is greatly appreciated


Oh, and sorry for the messy coding 🤣
If you have any issues, please tell me at Github Issues.

# Usage
Currently this library only supports three main API: Character, Post and User

Here is an example:
```python
from CharAI import *
from CharAI.helper import dump

def pass_check(x):
    if isinstance(x, CAI):
        return False
    return True

full_dumper = lambda x: (dict([(k, v) for k, v in vars(x).items() if not k.startswith('__') and pass_check(x)]) if hasattr(x, '__dict__') else str(x)) if pass_check(x) else "PASSED"

client = Client("xxxxx")
usermng = client.user_api()


me = usermng.self()

dump(me, default=full_json_dumper)

dump(me.recent_chat(), default=full_dumper)
dump(me.recent_chat2(), default=full_dumper)
dump(me.recent_rooms(), default=full_dumper)
```
