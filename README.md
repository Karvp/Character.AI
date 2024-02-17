# Character.AI
An unofficial high level API for character.ai for Python

# Introduction
The original idea was from [kramcat's CharacterAI](https://github.com/kramcat/characterai). This library aims on ease of use rather than a more functional library.
You can get the token to use in this library from your Character AI account. kramcat has made [a demonstration](https://github.com/kramcat/characterai?tab=readme-ov-file#-get-token) on it.

> [!NOTE]
> This library is developing, bugs may occur occasionally. Every contribution is greatly appreciated!


Sorry for the messy coding 🤣
If you have any issues, please tell me at Github Issues.

# Usage
Currently this library only supports querying with: Character, Post, User and Chat. You can make a post, comment on it, search information about characters, users, posts, or even chatting

Here is an example of getting basic information from the account:
```python
from CharAI import *
from CharAI.helper import dump

# don't mind this messy, it is just for dumpping attributes
def pass_check(x):
    if isinstance(x, CAI):
        return False
    return True

full_dumper = lambda x: (dict([(k, v) for k, v in vars(x).items() if not k.startswith('__') and pass_check(x)]) if hasattr(x, '__dict__') else str(x)) if pass_check(x) else "PASSED"

client = Client("YOUR_TOKEN_HERE")

me = client.User.self()

dump(me, default=full_json_dumper)

dump(me.recent_chat(), default=full_dumper)
dump(me.recent_chat2(), default=full_dumper)
dump(me.recent_rooms(), default=full_dumper)
```

And here is an example of chatting:
```python
from CharAI import *

client = Client("YOUR_TOKEN_HERE")

chat = client.Chat.open("CHARACTER_ID_HERE")

chat.voice = True
# we will turn on voice

message = Messaging.Object(client, "hello world", img=new.File("path/to/your/image"), img_descr="YOUR_IMAGE_DESCRIPTION")
# or you can use this as well
# message = client.Chat.msg("hello world", img=new.File("path/to/your/image"), img_descr="YOUR_IMAGE_DESCRIPTION")

# We will try to send our message
try:
    # the reply function is used to send message
    response = chat.reply(message)
    # if you have alternatives, you can select by its uuid
    # response = chat.reply(message, uuid="0000-0000-0000-0000")

    # the reply function returns a Response object, with its attributes: `replies` and `audios`
    # `audios` is the list of new.MP3 object, use new.MP3.binaries() to get the binaries
    # `replies` containing replies from the bot

    # to get alternative response, use chat.next()
    response = chat.next()
except errors.ServerError:
    print("Retrying...")
    try:
        # After you've sent the message for the first time, you can retry sending it like this
        response = message.retry()
    except errors.ServerError:
        print("Failed!")
```

# Documentation
Please check the comments I made in the code. Btw, if it is unclear, please notice me.
