import tls_client
import ujson as json
import copy
import inspect
from time import sleep, time
from enum import Enum
from datetime import datetime, timezone
from collections.abc import Collection

from CharAI import errors, helper, new

__all__ = ['Client']

BASE_IMAGE_PATH = "https://characterai.io/i/400/static/posts/images/"
BASE_AVATAR_URL = "https://characterai.io/i/80/static/avatars/"
BASE_TOPIC_AVATAR_URL = "https://characterai.io/i/80/static/topic-pics/"
BASE_POST_IMG_UPLOAD_PATH = "chat/post/img/upload/"
BASE_AVATAR_UPLOAD_PATH = "chat/avatar/upload/"

DEFAULT_LAST_MSG_PAGE = 1000000

ANONYMOUS = 'ANONYMOUS'

class Data(Enum):
    unknown = 1
UNKNOWN = Data.unknown

class Subcription(Enum):
    beta = 1
    plus = 2

class Post_type(Enum):
    chat = 1
    post = 2

class Visibility(Enum):
    PUBLIC = 'PUBLIC'
    UNLISTED = 'UNLISTED'
    PRIVATE = 'PRIVATE'
    VISIBILITY_PRIVATE = 'VISIBILITY_PRIVATE'

class Posts_sort(Enum):
    top = 'top'
    votes = 'votes'
    created = 'created' 

def parse_time(time: str|Data) -> datetime:
    """ Parses time string """
    return UNKNOWN if time == UNKNOWN else datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

def get_avatar(self, info: dict, pre: str = ''):
    """ Get and save an avatar """
    setattr(self, 'avatar', info.pop(pre + 'avatar_file_name', UNKNOWN))
    if self.avatar != UNKNOWN and self.avatar != None and len(self.avatar) > 0:
        self.avatar = BASE_AVATAR_URL + self.avatar
    setattr(self, 'avatar_type', info.pop(pre + 'avatar_type', UNKNOWN))

def get_img(self, info: dict):
    """ Get and save an image """
    setattr(self, 'image', info.pop('image_rel_path', UNKNOWN))
    if self.image != UNKNOWN and len(self.image) > 0:
        self.image = BASE_IMAGE_PATH + self.image

        

class Persona:
    pass

class Category:
    def __init__(self, **kwargs):
        self.name = kwargs.pop('name', UNKNOWN)
        self.description = kwargs.pop('description', UNKNOWN)
        self.priority = kwargs.pop('priority', UNKNOWN)

class Voice:
    def __init__(self, **kwargs):
        self.id = kwargs.pop('id', UNKNOWN)
        self.name = kwargs.pop('name', UNKNOWN)
        self.voice_id = kwargs.pop('voice_id', UNKNOWN)
        self.country = kwargs.pop('country_code', UNKNOWN)
        self.lang = kwargs.pop('lang_code', UNKNOWN)

class CAI:
    """ Character AI session """
    def __init__(self, token: str = None):
        """ Creates a new session """
        self.session = tls_client.Session(client_identifier='chrome112')
        self.sub = Subcription.beta
        self.timestamp: float = time()
        if token != None:
            self.token = token
            self.get_sub()

    def get_sub(self):
        """ Get and save current account's subcription """
        if self.token != None:
            info = self.info()['user']['user']
            if info['username'] == ANONYMOUS:
                raise errors.AuthError("Invalid token")
            self.sub = Subcription.beta if info['subscription'] == None else Subcription.plus
    
    def ping(self):
        """ Ping character AI """
        return self.session.get('https://neo.character.ai/ping/').json()
    
    def set_token(self, token: str):
        """ Set the token """
        self.token = token
        self.get_sub()

    def request(self, path: str, *, neo: bool = False, method: str = 'GET', split: bool = False, **kwargs):
        """ Perform a request """

        if neo:
            url = f'https://neo.character.ai/{path}'
        else:
            url = f'https://{self.sub.name}.character.ai/{path}'
        headers = {
            'Authorization': f'Token {self.token}'
        }
        if method == 'GET':
            res = self.session.get(url, headers=headers, **kwargs)
        elif method == 'POST':
            res = self.session.post(url, headers=headers, **kwargs)
        elif method == 'PUT':
            res = self.session.put(url, headers=headers, **kwargs)
        jres: dict = json.loads(res.text)
        if jres.get('neo_error', UNKNOWN) != UNKNOWN:
            raise errors.ServerError(jres["comment"])
        elif jres.get('detail', UNKNOWN) != UNKNOWN and jres['detail'].startswith('Auth'):
            raise errors.AuthError("Invalid token")
        elif jres.get('status', UNKNOWN) != UNKNOWN and jres['status'].startswith('Error'):
            raise errors.ServerError(jres["status"])
        elif jres.get('error', UNKNOWN) != UNKNOWN:
            raise errors.ServerError(jres["error"])
        else:
            return jres if not split else json.loads(res.text.split('\n')[-2])
    
    def upload_files(self, path: str, files: list[tuple[str, helper.File]]):
        """ Upload files """

        url = f'https://{self.sub.name}.character.ai/{path}'
        
        uploader = helper.FileUploader(self.session)
        try:
            for name, file in files:
                uploader.addFile(name, file)
        except Exception as e:
            raise errors.UnexpectedError("Failed to add files") from e
            
        try:
            res = uploader.upload(url, headers={
                'Authorization': f'Token {self.token}'
            }).text
        except Exception as e:
            raise errors.CAIError("Failed to upload files") from e
        
        res: dict = json.loads(res.text)
        if res.get('neo_error', UNKNOWN) != UNKNOWN:
            raise errors.ServerError(res["comment"])
        elif res.get('detail', UNKNOWN) != UNKNOWN and res['detail'].startswith('Auth'):
            raise errors.AuthError("Invalid token")
        elif res.get('status', UNKNOWN) != UNKNOWN and res['status'].startswith('Error'):
            raise errors.ServerError(res["status"])
        elif res.get('error', UNKNOWN) != UNKNOWN:
            raise errors.ServerError(res["error"])
        else:
            return res
    
    def info(self):
        """ Get current account's information """
        if self.token == None:
            raise errors.AuthError("Missing API token")
        return self.request('chat/user/')
    
    def test_connection(self):
        """ Test the connection to server """
        count = 0
        stat = self.ping()['status']
        while stat != 'pong' and count < 10:
            print("Reconnecting to the server...")
            sleep(1)
            count += 1
            stat = self.ping()['status']
        if count == 10 and stat != 'pong':
            raise errors.ConnectionError("Failed to connect to the server")


class Authenticated(CAI):
    """ An authenticated Character AI session """
    def __init__(self, token: str):
        super().__init__(token=token)
        self.test_connection()
        self.user = User.User(self)
        
class Anonymous(CAI):
    """ An anonymous Character AI session """
    username = ANONYMOUS
    def __init__(self):
        super().__init__()
        self.test_connection()
    def get_shared_messages(self, history_id: str):
        return self.cai.request(f'chat/history/external/msgs/?history={history_id}')
         
class Owner:
    """ Group of classes containing owner's information """
    class Character:
        """ Character's owner information """
        pass

    class Post:
        """ Post's owner information """
        def __init__(self, cai: Authenticated, info: dict):
            self.cai = cai
            
            self.name = info.pop('poster_name', UNKNOWN)
            self.username = info.pop('poster_username', UNKNOWN)
            self.is_staff = info.pop('poster__is_staff', UNKNOWN)
            get_avatar(self, info, 'poster_')
            self.subscription = Subcription.beta if info.pop('poster_subscription_type', "NONE") == "NONE" else Subcription.plus

    class Comment:
        """ Comment's owner information """
        def __init__(self, cai: Authenticated, info: dict):
            self.cai = cai
            
            self.name = info.pop('src__name', UNKNOWN)
            self.username = info.pop('src__user__username', UNKNOWN)
            get_avatar(self, info, 'src__user__account__')
            self.is_staff = info.pop('src__user__is_staff', UNKNOWN)
            self.subscription = Subcription.beta if info.pop('src__user_subscription_type', None) == None else Subcription.plus
            
    class Message:
        """ Message's owner information """
        def __init__(self, info: dict):
            self.src = info.pop('src', UNKNOWN)
            get_avatar(self, info, 'src__character__')
            self.is_human = info.pop('src__is_human', UNKNOWN)
            self.name = info.pop('src__name', UNKNOWN)
            self.username = info.pop('src__user__username', UNKNOWN)

    class Custom:
        """ Custom owner information """
        def __init__(self, *, __dict: dict = None, **kwargs):
            if __dict == None:
                for k, v in kwargs.items():
                    setattr(self, k, v)
            else:
                for k, v in __dict.items():
                    setattr(self, k, v)

class History:
    """ Access to data saved on the server """
    CHAT = 1
    POST = 2
    def __init__(self, cai: Authenticated, source: int, *, external_id: str = None, type: str = None):
        self.__cai = cai
        self.source = source
        self.external_id = external_id
        self.type = type

    def load(self, info: dict):
        """ Load data's information """
        if self.source == History.POST:
            self.external_id = info.pop('attached_history__external_id', UNKNOWN)
            self.type = info.pop('attached_history__type', UNKNOWN)
        elif self.source == History.CHAT:
            self.external_id = info.pop('external_id', UNKNOWN)
            self.type = info.pop('type', UNKNOWN)
        else:
            raise errors.ValueError("Unknown history's source")
        
    def get_messages(self, page: int = DEFAULT_LAST_MSG_PAGE) -> dict:
        """ Get saved messages """
        if self.source == History.POST:
            return self.__cai.request(f'chat/history/external/msgs/?history={self.external_id}&page_num={page}')
        elif self.source == History.CHAT:
            return self.__cai.request(f'chat/history/external/msgs/user/?history={self.external_id}&page_num={page}')

                 
class Comment:
    """ Represents a comment """
    def __init__(self, cai: Authenticated, post_external_id: str, parent, info: dict):
        self.__cai = cai
        self.parent = parent
        self.post_external_id = post_external_id
        self.__load_info(info)

    def __load_info(self, info: dict):
        """ Load comment's information from the api """
        get_img(self, info)
        self.created = parse_time(info.pop('created', UNKNOWN))
        self.id: int = info.pop('id', UNKNOWN)
        self.reject_instead_of_delete: bool = info.pop('is_reject_instead_of_delete', UNKNOWN)
        self.user = Owner.Comment(info)
        self.text: str = info.pop('text', UNKNOWN)
            
        self.uuid: str = info.pop('uuid', UNKNOWN)
        self.comments = [Comment(self.cai, self.post_external_id, self, data) for data in info.pop("children", [])]
        
        self.deletable: bool = info.pop('deleting_enabled', UNKNOWN)
        if self.deletable != True:
            @classmethod
            def deleted(self):
                raise errors.UnexpectedError("This comment has been deleted")
            
            self.remove = deleted
            self.comment = deleted

    def is_owner(self, user) -> bool:
        """ Check if an user is the owner of this comment """
        return self.user.username == user.username

    def __validate_owner(self, alter: Authenticated = None, err_msg: str = errors.DEFAULT_ERROR_MSG) -> Authenticated:
        """ Validate user's permission to this comment """
        if alter == None:
            if not self.is_owner(self.__cai.user):
                raise errors.PermissionError(err_msg if err_msg != None else "Failed!")
            return self.__cai
        else:
            if not self.is_owner(alter.user):
                raise errors.PermissionError(err_msg)
            return alter

    def remove(self, cai: Authenticated = None) -> bool:
        """ Remove this comment """
            
        return self.__validate_owner(cai, "You do not have permission to delete this comment")\
        .request(
            'chat/comment/delete/', method='POST',
            json={
                'external_id': self.id,
                'post_external_id': self.post_external_id
            }
        )["success"]
    
    def comment(self, text: str) -> bool:
        """ Comment on this comment """

        return self.__cai.request(
            'chat/comment/create/', method='POST',
            json={
                'post_external_id': self.post_external_id,
                'text': text,
                'parent_uuid': self.parent.uuid
            }
        )["success"]
    
class Post:
    class Template:
        def _get_info(self) -> dict:
            """ Get the raw api result """
            return self.cai.request(
                f'chat/post/?post={self.external_id}'
            )
        
        def _reset(self):
            """ Reset SOME informations """
            self.comments = []
            self.external_id = UNKNOWN
            self.comments_count = UNKNOWN
            self.id = UNKNOWN
            self.uuid = None
            self.text = UNKNOWN
            self.title = UNKNOWN
            self.upvotes = UNKNOWN
            self.visibility = UNKNOWN
            self.locked = UNKNOWN
            self.pinned = UNKNOWN
            self.upvoted = UNKNOWN
            self.deletable = UNKNOWN
            self.history = UNKNOWN
            self.created = UNKNOWN
            self.updated = UNKNOWN

        def is_posted_by(self, user) -> bool:
            """ Check is owner """
            return self.poster.username == user.username
        
        def comment(self, text) -> dict:
            """ Comment on this post """
            return self.cai.request(
                'chat/comment/create/', method='POST',
                json={
                    'post_external_id': self.external_id,
                    'text': text,
                    'parent_uuid': None
                }
            )
        
        def upvote(self) -> bool:
            """ Upvote this post """
            return self.cai.request('chat/post/upvote/', method='POST', json={
                'post_external_id': self.external_id
            })['success']
        
        def undo_upvote(self) -> bool:
            """ Undo upvote this post """
            return self.cai.request('chat/post/undo-upvote/', method='POST', 
                json={'post_external_id': self.external_id}
            )['success']
        
    class Post(Template):
        def __init__(self, cai: Authenticated, external_id: str):
            self.cai = cai
            self._reset()
            
            self.external_id = external_id
            self.__load_info(self._get_info())
          
        def __load_info(self, info: dict) -> None:
            self.comments = [Comment(self.cai, self.external_id, self, cmt) for cmt in info.pop('comments', [])]
            info = info.pop('post', dict())
            
            self.external_id = info.pop('external_id', UNKNOWN)
            self.id = info.pop('id', UNKNOWN)
            
            # Parse some metadata and post content
            self.text = info.pop('text', UNKNOWN)
            self.title = info.pop('title', UNKNOWN)
            self.upvotes = info.pop('upvotes', UNKNOWN)
            # Some status/state
            self.visibility = info.pop('visibility', Visibility.PUBLIC)
            self.visibility = getattr(Visibility, self.visibility, self.visibility)
            
            self.locked = info.pop('is_locked', UNKNOWN)
            self.pinned = info.pop('is_pinned', UNKNOWN)
            self.upvoted = info.pop('is_upvoted', UNKNOWN)
            self.pinable = info.pop('pinning_enabled', UNKNOWN)
            self.deletable = info.pop('deleting_enabled', UNKNOWN)
            self.reject_instead_of_delete = info.pop('is_reject_instead_of_delete', UNKNOWN)
            # get history external id to get messages
            self.history = History(self.cai, History.post)
            self.history.load(info)
            
            # get created date
            self.created = parse_time(info.pop('created', UNKNOWN))
            # Parse the poster info
            self.poster = Owner.Post(self.cai, info)
        
            self.topic_id = info.pop('topic__external_id', UNKNOWN)
            get_img(self, info)
            self.updated = parse_time(info.pop('updated', UNKNOWN))
            
        def reload(self):
            self.__load_info(self._get_info())
            return self
        
        def remove(self) -> bool:
            return self.cai.request('chat/post/delete/', method='POST',
                json={'external_id': self.external_id}
            )['success']
        
    class Topic(Template):
        def __init__(self, cai: Authenticated, info: dict):
            self.cai = cai
            self._reset()
            
            self.__load_info(info)
            
        def __load_info(self, info: dict) -> None:
            self.external_id = info.pop('external_id', UNKNOWN)
            self.id = info.pop('id', UNKNOWN)
            
            # Parse some metadata and post content
            self.text = info.pop('text', UNKNOWN)
            self.title = info.pop('title', UNKNOWN)
            self.upvotes = info.pop('upvotes', UNKNOWN)
            # Some status/state
            self.visibility = Visibility.PUBLIC
            self.locked = info.pop('is_locked', UNKNOWN)
            self.pinned = info.pop('is_pinned', UNKNOWN)
            self.upvoted = info.pop('is_upvoted', UNKNOWN)
            self.pinable = info.pop('pinning_enabled', UNKNOWN)
            self.deletable = info.pop('deleting_enabled', UNKNOWN)
            self.reject_instead_of_delete = info.pop('is_reject_instead_of_delete', UNKNOWN)
            # get history external id to get messages
            self.history = History(self.cai, History.post)
            self.history.load(info)
            # get created date
            self.created = parse_time(info.pop('created', UNKNOWN))
            # Parse the poster info
            self.poster = Owner.Post(self.cai, info)
        
            self.updated = parse_time(info.pop('updated', UNKNOWN))
            
            # Other informations
            self.messages_shard = info.pop('messages_shard', UNKNOWN)
            self.seen = info.pop('seen', UNKNOWN)
            
        def get_full_post(self):
            return Post.Post(self.cai, self.external_id)
            
    class UserPage(Template):
        def __init__(self, cai: Authenticated, info: dict):
            self.cai = cai
            self._reset()
            
            self.__load_info(info)

        def __load_info(self, info: dict) -> None:
            self.external_id = info.pop('external_id', UNKNOWN)
            self.id = info.pop('id', UNKNOWN)
            
            # Parse some metadata and post content
            self.text = info.pop('text', UNKNOWN)
            self.title = info.pop('title', UNKNOWN)
            self.upvotes = info.pop('upvotes', UNKNOWN)
            # Some status/state
            self.visibility = Visibility.PUBLIC
            self.locked = info.pop('is_locked', UNKNOWN)
            self.pinned = info.pop('is_pinned', UNKNOWN)
            self.upvoted = info.pop('is_upvoted', UNKNOWN)
            self.deletable = info.pop('deleting_enabled', UNKNOWN)
            # get history external id to get messages
            self.history = History(self.cai, History.post)
            self.history.load(info)
            # get created date
            self.created = parse_time(info.pop('created', UNKNOWN))
            # Parse the poster info
            self.poster = Owner.Post(self.cai, info)
        
            self.updated = parse_time(info.pop('updated', UNKNOWN))
            
            # Other informations
            self.messages_shard = info.pop('messages_shard', UNKNOWN)
            self.comments_count = info.pop('comments_count', UNKNOWN)
            
        def get_full_post(self):
            return Post.Post(self.cai, self.external_id)

class Character:
    NO_PERMISSION = "do not have permission to view this Character"
    UNAUTHORIZED = 'unauthorized'
    NOT_OK = 'NOT_OK'


    class Visible:
        """ Parent class for visible characters' class """
        VISIBLE = True
        
    class Owning(Visible):
        """ Parent class for owning characters' class """
        IS_MINE = True
        CONTROLLABLE = True
        
    class Public(Visible):
        """ Parent class for public characters' class """
        PUBLIC = True
        def is_owned_by(self, user):
            return self.creator == user.username
        
        def get_control(self, user = None):
            # user: User.Me = user
            if user == None:
                if not self.is_owned_by(self.cai.user):
                    raise errors.PermissionError(f"{self.cai.user.username} does not have permission to controll this character")
                return Character.Character(self.cai, self.external_id, __safe_init=True)
            else:
                if not self.is_owned_by(user):
                    raise errors.PermissionError(f"{user.username} do not have permission to controll this character")
                return Character.Character(user.cai, self.external_id, __safe_init=True)
            
    class Informative(Visible):
        """ Parent class for info-only classes """
        CONTROLLABLE = False
    
    class Info(Public, Informative):
        """ Represents a public character 
        
        Attributes:
            
            - `name`                Name of the character
            - `title`               Title of the character
            - `greeting`            Character's greeting message
            - `copyable`            Is the character copyable or not
            - `description`         The character's description
            - `img_gen`             Indicates if character's image generation is enabled or not
            - `base_img_prompt`     The base prompt to generate image
            - `img_prompt_re`       I do not know ;)
            - `hide_image_prompt`   Indicates if the image prompt to generate message (not the base prompt) is hidden or not
            - `visibility`          The visibility of the character
            - `starter_prompts`     Starter prompts for the user
            - `voice_id`            The character's voice

        """
        def __init__(self, cai: Authenticated, external_id: str):
            self.__cai = cai
            self._external_id = external_id
            self.__load_info(cai.request(
                'chat/character/info/', method='POST',
                json={'external_id': external_id}
            ))
            
        def __load_info(self, info: dict):
            if info.get('status') == Character.NOT_OK:
                if info['error'] == Character.UNAUTHORIZED:
                    raise errors.PermissionError("You do not have permission to view this character")
                else:
                    raise errors.ServerError(info['error'])
                
            info = info.pop('character', dict())
            get_avatar(self, info)
        
            self.name: str = info.pop('name', UNKNOWN)
            self.title: str = info.pop('title', UNKNOWN)
            self.greeting: str = info.pop('greeting', UNKNOWN)
            self.copyable: bool = info.pop('copyable', UNKNOWN)
            self.description: str = info.pop('description', UNKNOWN)
        
            self.img_gen: str = info.pop('img_gen_enabled', UNKNOWN)
            self.base_img_prompt: str = info.pop('base_img_prompt', UNKNOWN)
            self.img_prompt_re: str = info.pop('img_prompt_regex', UNKNOWN)
            self.hide_image_prompt: bool = info.pop('strip_img_prompt_from_msg', UNKNOWN)
            
            self.visibility = info.pop('visibility', UNKNOWN)
            self.visibility: Visibility | str = getattr(Visibility, self.visibility, self.visibility)
        
            self.starter_prompts: dict[str, list[str]] = info.pop('starter_prompts', {'phrases': []})
            self.voice_id: int = info.pop('voice_id', UNKNOWN)
        
            self._usage: str = info.pop('usage', UNKNOWN)
            self._identifier: str = info.pop('identifier', UNKNOWN)
            self._songs: list = info.pop('songs', [])
            self._default_voice_id = info.pop('default_voice_id', UNKNOWN)
            self._creator: Owner.Custom = Owner.Custom(username=info.pop('user__username'))
            self._username: str = info.pop('participant__user__username', UNKNOWN)
            self._interactions: int = info.pop('participant__num_interactions', UNKNOWN)
        
        @property
        def interactions(self):
            """ Returns the number of interactions """
            return self._interactions
        
        @property
        def username(self):
            """ Returns the character's username """
            return self._username
        
        @property
        def creator(self):
            """ Returns the character's creator detail class """
            return self._creator
        
        @property
        def external_id(self):
            """ Returns the character's external id """
            return self._external_id
        
        @property
        def usage(self):
            """ Returns the character's usage """
            return self._usage
        
        @property
        def identifier(self):
            """ Returns the character's identifier """
            return self._identifier
        
        @property
        def songs(self):
            """ Returns the character's songs """
            return self._songs
        
        @property
        def default_voice_id(self):
            """ Returns the character's default voice id """
            return self._default_voice_id
            
    class PublicCharacter(Public, Informative):
        """ Still represents a public character, but less detailed """
        def __init__(self, info: dict):
            self.__load_info(info)
            
        def __load_info(self, info: dict):

            get_avatar(self, info)

            self.copyable: bool = info.pop('copyable', UNKNOWN)
            self.description: str = info.pop('description', UNKNOWN)
            self.external_id: str = info.pop('external_id', UNKNOWN)
            self.greeting: str = info.pop('greeting', UNKNOWN)  
            self.img_gen: int = info.pop('img_gen_enabled', UNKNOWN)
            self.name: str = info.pop('participant__name', UNKNOWN)
            self.interactions: int = info.pop('participant__num_interactions', UNKNOWN)
            self.remixes: int = info.pop('remix_count', UNKNOWN)
            self.title: str = info.pop('title', UNKNOWN)
            
            self.creator: Owner.Custom = Owner.Custom(id=info.pop('user__id', UNKNOWN), username=info.pop('user__username', UNKNOWN))
            
            self.visibility = info.pop('visibility', UNKNOWN)
            self.visibility: Visibility | str = getattr(Visibility, self.visibility, self.visibility)
       
    class MyCharacter(Owning, Informative):
        def __init__(self, cai: Authenticated, info: dict):
            self.__cai = cai
            self.__load_info(info)
            
        def __load_info(self, info: dict):
            
            get_avatar(self, info)
            
            self.copyable: bool = info.pop('copyable', UNKNOWN)
            self.definition: str = info.pop('definition', UNKNOWN)
            self.description: str = info.pop('description', UNKNOWN)
            self.greeting: str = info.pop('greeting', UNKNOWN)
            self.img_gen: bool = info.pop('img_gen_enabled', UNKNOWN)
            self.name: str = info.pop('participant__name', UNKNOWN)
            self.title: str = info.pop('title', UNKNOWN)
            self.visibility = info.pop('visibility', UNKNOWN)
            self.visibility: Visibility | str = getattr(Visibility, self.visibility, self.visibility)
            
            self._interactions: int = info.pop('participant__num_interactions', UNKNOWN)
            self._remixes: int = info.pop('remix_count', UNKNOWN)
            self._creator: Owner.Custom = Owner.Custom(id=info.pop('user__id', UNKNOWN), username=info.pop('user__username', UNKNOWN))
            self._external_id: str = info.pop('external_id', UNKNOWN)
            
        def update(self, *, starter_prompts: dict[str, list[str]], base_prompt: str, hide_prompt: bool, voice: Voice, categories: list[Category]) -> bool:
            return self.__cai.request(
                'chat/character/update/', method='POST',
                json={
                    'external_id': self.external_id,
                    'name': self.name,
                    'categories': [c.name for c in categories],
                    'title': self.title,
                    'visibility': self.visibility,
                    'copyable': self.copyable,
                    'description': self.description,
                    'greeting': self.greeting,
                    'definition': self.definition,
                    'starter_prompts': starter_prompts,
                    'img_gen_enabled': self.image_generation,
                    'base_img_prompt': base_prompt,
                    'strip_img_prompt_from_msg': hide_prompt,
                    'voice_id': voice.id
                }
            )['status'] == "OK"

        def get_full_control(self):
            return Character.Character(self.__cai, self.external_id, __safe_init=True)
        
        @property
        def interactions(self):
            return self._interactions
        
        @property
        def remixes(self):
            return self._remixes
        
        @property
        def creator(self):
            return self._creator
        
        @property
        def external_id(self):
            return self._external_id

    class Character(Owning, Info):
        """ A class help you get and modify information of the character """

        def __init__(self, cai: Authenticated, external_id: str, *, __safe_init: bool = False):
            super().__init__(cai, external_id)
            
            if not __safe_init and self.creator != cai.user.username:
                raise errors.PermissionError("You do not have permission to access this character")

            self.__load_info(cai.request(
                'chat/character/', method='POST',
                json={'external_id': external_id}
            ))

        def __load_info(self, info: dict):
            if info.get('status') == Character.NO_PERMISSION:
                raise errors.PermissionError(info['status'])
            
            info = info.pop('character', dict())
            get_avatar(self, info)

            self.definition: str = info.pop('definition', UNKNOWN)
            self.categories = [Category(**category) for category in info.pop('categories', [])]
        
        def update(self) -> bool:
            return self.__cai.request(
                'chat/character/update/', method='POST',
                json={
                    'external_id': self.external_id,
                    'name': self.name,
                    'categories': [c.name for c in self.categories],
                    'title': self.title,
                    'visibility': self.visibility,
                    'copyable': self.copyable,
                    'description': self.description,
                    'greeting': self.greeting,
                    'definition': self.definition,
                    'starter_prompts': self.starter_prompts,
                    'img_gen_enabled': self.img_gen,
                    'base_img_prompt': self.base_img_prompt,
                    'strip_img_prompt_from_msg': self.hide_image_prompt,
                    'voice_id': self.voice
                }
            )['status'] == "OK"
        
        def set_voice(self, voice: Voice|int):
            if isinstance(voice, int):
                self.voice = voice
            else:
                self.voice = voice.id
            
        def add_starter_phrase(self, phrase: str):
            self.starter_prompts['phrases'].append(phrase)
            
        def get_starter_phrases(self):
            return self.starter_prompts['phrases']
    
        
class Topic:
    """ Represents a topic """
    def __init__(self, cai: Authenticated, info: dict = None, external_id: str = None):
        self.__cai = cai
        if info != None:
            self.load_info(info)
        elif external_id != None:
            self.external_id = external_id
        else:
            raise errors.ValueError("Invalid topic")
        
    def load_info(self, info: dict):
        """ Load topic's info"""
        get_avatar(self, info)
        self.description = info.pop('description', UNKNOWN)
        self.external_id = info.pop('external_id', UNKNOWN)
        self.name = info.pop('name', UNKNOWN)
        self.unseen_posts_count = info.pop('unseen_posts_count', UNKNOWN)
        
    def get_posts(self, *, page: int = 1, loads: int = 1, sort: Posts_sort = Posts_sort.top) -> dict[str, list[Post.Topic]|bool]:
        """ Get latest posts on the topic """
        data = self.__cai.request(
            f'chat/posts/?topic={self.external_id}&page={page}'
            f'&posts_to_load={loads}&sort={sort}'
        )
        return {
            'posts': [
                Post.Topic(self.__cai, info)
                for info in data.get('posts', [])
            ], 
            'posting_enabled': data['topic']['posting_enabled'], 
            'has_more': data['has_more']
        }
    
    def post(self, post: new.Post, cai: Authenticated = None):
        """ Posts a new post """
        if cai == None:
            cai = self.__cai
        data = {
            'post_title': post.title,
            'topic_external_id': self.external_id,
            'post_text': post.text,
            **post.options
        }
        if post.image != None:
            info = cai.upload_files('chat/post/img/upload/', files=('img', post.image))
            if info['status'] != 'OK':
                raise errors.ServerError(info['status'])
            data['image_rel_path'] = info['value']
            
        return Post(cai,
            cai.request(
                'chat/post/create/', 
                method="POST", 
                json=data
            )['post']['external_id']
        )

class Feed:
    """ Represents the feed """
    EX_ID = 'gLj1MBqU6AgCuf4IwUE-5q4Vz-CKMP5be23HERh0Ekg'
    def __init__(self, cai: Authenticated):
        self.__cai = cai

    def get_posts(self, *, page: int = 1, loads: int = 1, sort: Posts_sort = Posts_sort.top):
        """ Get latest posts from the feed """
        data = self.__cai.request(
            f'chat/posts/?topic={Feed.EX_ID}&page={page}'
            f'&posts_to_load={loads}&sort={sort}'
        )     
        return {
            'posts': [
                Post.Topic(self.cai, info)
                for info in data.get('posts', [])
            ], 
            'posting_enabled': data['topic']['posting_enabled'], 
            'has_more': data['has_more']
        }
                
class User:
    """ Group of user classes """
    class Me:
        """ Represents the current user """
        def __init__(self, cai: Authenticated, preload: bool = True):
            self.__cai = cai
            if preload:
                self.__load_info(self.__cai.request('chat/user/'))
            
        def __load_info(self, info: dict):
            """ Loads user's information from the api """

            info = info.pop('user', dict())
            self.bio = info.pop('bio', UNKNOWN)
            self.name = info.pop('name', UNKNOWN)
            self.email = info.pop('email', UNKNOWN)
            self.is_human = info.pop('is_human', UNKNOWN)
            self.blocked_users = info.pop('blocked_users', UNKNOWN)
            self.suspended_until = info.pop('suspended_until', UNKNOWN)
            self.hidden_characters = info.pop('hidden_characters', UNKNOWN)
            
            info = info.pop('user', dict())
            self.subscription = self.__cai.sub
            self.id = info.pop('id', UNKNOWN)
            self.username = info.pop('username', UNKNOWN)
            self.is_staff = info.pop('is_staff', UNKNOWN)
            self.first_name = info.pop('first_name', UNKNOWN)
            
            info = info.pop('account', dict())
            get_avatar(self, info)

        def follow(self, username: str):
            """ Follow somebody """
            return self.__cai.request('chat/user/follow/', method='POST', json={'username': username})
        
        def unfollow(self, username: str):
            """ Unfollow somebody """
            return self.__cai.request('chat/user/unfollow/', method='POST', json={'username': username})
        
        def followers(self):
            """ Get user's followers """
            return self.__cai.request('chat/user/followers/')
        
        def following(self):
            """ Get user's followings """
            return self.__cai.request('chat/user/following/')
        
        def recent_chat(self):
            """ Get user's recent chats from chat api """
            return self.__cai.request('chat/characters/recent/')
        
        def recent_rooms(self):
            """ Get user's recent chat rooms from chat api """
            return self.__cai.request('chat/rooms/recent/')
        
        def recent_chat2(self):
            """ Get user's recent chats from chat2 api """
            return self.__cai.request('chats/recent/', neo=True)
        
        def characters(self):
            """ Get user's characters """
            return [
                Character.MyCharacter(self.__cai, info)
                for info in 
                self.__cai.request('chat/characters/?scope=user').pop('characters', [])
            ]
        
        def update(self, *, avatar: new.File = None, bio: str = None, name: str = None, username: str = None):
            """ Update user's information """
            if avatar == None and bio == None and name == None and username == None:
                return False
            
            data = {'avatar_type':"DEFAULT"}
            
            if avatar == None:
                imgurl = self.avatar
            else:
                info = self.__cai.upload_files(BASE_AVATAR_UPLOAD_PATH, files=[('image', avatar)])
                if info['status'] != 'OK':
                    raise errors.ServerError(info['error'])
                imgurl = info['value']
            data['avatar_rel_path'] = imgurl
                
            if bio == None:
                bio = self.bio
            data['bio'] = bio
            
            if name == None:
                name = self.name
            data['name'] = name
            
            if username == None:
                username = self.username
            data['username'] = username
            
            res = self.__cai.request('chat/user/update/', 
                method='POST', json=data)['status'] == "OK"
            
            if res:
                self.avatar = imgurl
                self.bio = bio
                self.name = name
                self.username = username
                
            return res
        
        def __raw_posts(self, page: int = 1, loads: int = 5):
            return self.__cai.request(f'chat/posts/user/?scope=user&page={page}&posts_to_load={loads}/').pop('posts', [])

        def posts(self, *, page: int = 1, loads: int = 5) -> list[Post.UserPage]:
            """ Get user's posts"""
            return [
                Post.UserPage(self.__cai, info)
                for info in 
                self.__raw_posts(page, loads)
            ]
        
    class Other:
        """ Represents a public profile """
        def __init__(self, cai: Authenticated, username: str):
            self.__cai = cai
            self.__load_info(self.cai.request(
                'chat/user/public/', method="POST",
                json={'username': username}
            ))

        def __load_info(self, info: dict):
            """ Load user's information from api """

            info = info.pop('user', dict())
            self.bio = info.pop('bio', UNKNOWN)
            self.name = info.pop('name', UNKNOWN)
            self.username = info.pop('username', UNKNOWN)
            self.followers = info.pop('num_followers', UNKNOWN)
            self.following = info.pop('num_following', UNKNOWN)
            self.subscription = Subcription.beta if info.pop('subscription_type', "NONE") == "NONE" else Subcription.plus
            self.characters = [Character.Public(data) for data in info.pop('characters', [])]
            get_avatar(self,info)
            self.is_staff = info.pop('_is_staff', UNKNOWN)
        
        def __raw_get_posts(self, page: int = 1, loads: int = 5):
            return self.__cai.request(f'chat/posts/user/?username={self.username}&page={page}&posts_to_load={loads}/').pop('posts', [])

        def get_posts(self, *, page: int = 1, loads: int = 5) -> list[Post.UserPage]:
            """ Get user's posts """
            return [
                Post.UserPage(self.__cai, info)
                for info in 
                self.__raw_get_posts(page, loads)
            ]
        
    class User(Me):
        """ Contains user's information, but attributes are locked """
        def __init__(self, cai: Authenticated):
            super().__init__(cai)
            self.__prepare()

        def __prepare(self):
            """ Lock attributes """
            @property
            def bio(self):
                return self._bio
            @property
            def name(self):
                return self._name
            @property
            def email(self):
                return self._email
            @property
            def is_human(self):
                return self._is_human
            @property
            def blocked_users(self):
                return self._blocked_users
            @property
            def suspended_until(self):
                return self._suspended_until
            @property
            def hidden_characters(self):
                return self._hidden_characters
            @property
            def subscription(self):
                return self._subscription
            @property
            def id(self):
                return self._id
            @property
            def username(self):
                return self._username
            @property
            def is_staff(self):
                return self._is_staff
            @property
            def first_name(self):
                return self._first_name
            @property
            def avatar(self):
                return self._avatar
            @property
            def avatar_type(self):
                return self._avatar_type

            delattr(self, '_Me__cai')

            attrs = [a for a in dir(self) if not a[0] == '_' and not inspect.ismethod(getattr(self, a))]
            for attr in attrs:
                setattr(self, "_" + attr, getattr(self, attr))
                delattr(self, attr)
                setattr(self, attr, locals()[attr])
            
        

Owner.Character = User.Other


# Working...
class Message:
    """ Represents a message """
    def __init__(self, chat, info: dict, pos: int):
        self.chat: Chat = chat # :v just for type hinting
        self.history = chat.history
        self.__cai = chat.cai
        self.pos = pos
        self.__load_info(info)
        
    def __load_info(self, info: dict):
        """ Load message's information from api """
        self.deleted = info.pop('deleted', UNKNOWN)
        self.id = info.pop('id', UNKNOWN)
        self.image_prompt = info.pop('image_prompt_text', UNKNOWN)
        get_img(self, info)
        self.is_alternative = info.pop('is_alternative', UNKNOWN)
        self.text = info.pop('text', UNKNOWN)
        self.uuid = info.pop('uuid', UNKNOWN)
        self.sender = info.pop('src__user__username', UNKNOWN)
        self.is_users_message = self.cai.user.username == self.sender
        if self.is_users_message:
            def block(self):
                raise errors.CAIError("This is not character's message")
        
    def next(
            self, parent, *, 
            ranking_method = "random", 
            staging = False,
            model_server_address = None,
            model_server_address_exp_chars = None,
            override_prefix = None,
            rooms_prefix_method = "",
            override_rank = None,
            rank_candidates = None,
            filter_candidates = None,
            unsanitized_characters = None,
            prefix_limit = None,
            prefix_token_limit = None,
            stream_params = None,
            traffic_source = None,
            model_properties_version_keys = "",
            enable_tti = None,
            initial_timeout = None,
            insert_beginning = None,
            stream_every_n_steps = 16,
            is_proactive = False,
            image_rel_path = "",
            image_description = "",
            image_description_type = "",
            image_origin_type = "",
            parent_msg_uuid = None,
            primary_msg_uuid = None,
            seen_msg_uuids = [],
            retry_last_user_msg_uuid = None,
            num_candidates = 1,
            give_room_introductions = True,
            mock_response = False,
            **kwargs
        ):
        if not self.active:
            raise errors.CAIError("The chat isn't active")
        data = self.__cai.request(
            'chat/streaming/', method="POST",
            split=True,
            json={
                "history_external_id": self.history.external_id,
                "character_external_id": self.char.external_id,
                "text": self.text,
                "tgt": self.char.username,
                "ranking_method": ranking_method,
                "staging": staging,
                "model_server_address": model_server_address,
                "model_server_address_exp_chars": model_server_address_exp_chars,
                "override_prefix": override_prefix,
                "rooms_prefix_method": rooms_prefix_method,
                "override_rank": override_rank,
                "rank_candidates": rank_candidates,
                "filter_candidates": filter_candidates,
                "unsanitized_characters": unsanitized_characters,
                "prefix_limit": prefix_limit,
                "prefix_token_limit": prefix_token_limit,
                "stream_params": stream_params,
                "traffic_source": traffic_source,
                "model_properties_version_keys": model_properties_version_keys,
                "enable_tti": enable_tti,
                "initial_timeout": initial_timeout,
                "insert_beginning": insert_beginning,
                "stream_every_n_steps": stream_every_n_steps,
                "is_proactive": is_proactive,
                "image_rel_path": image_rel_path,
                "image_description": image_description,
                "image_description_type": image_description_type,
                "image_origin_type": image_origin_type,
                "voice_enabled": self.chat.voice_enabled,
                "parent_msg_uuid": parent_msg_uuid,
                "primary_msg_uuid": primary_msg_uuid,
                "seen_msg_uuids": seen_msg_uuids,
                "retry_last_user_msg_uuid": retry_last_user_msg_uuid,
                "num_candidates": num_candidates,
                "give_room_introductions": give_room_introductions,
                "mock_response": mock_response,
                **kwargs
            }
        )
        
    def __add_info(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def remove(self) -> bool:
        """ Delete this message """

        return self.__cai.request(
            'chat/history/msgs/delete/',
            method='POST',
            json={
                "history_id": self.history.external_id,
                "uuids_to_delete": [self.uuid]
            }
        )['status'] == "OK"

# Working... 
class MessagePage:
    """ A page of up to 20 messages """
    def __init__(self, chat, page: int):
        self.chat: Chat = chat
        self.history = self.chat.history
        self.page = page
        self.pos = (DEFAULT_LAST_MSG_PAGE - page) * 20
        
        info = self.history.get_messages(page)
        self.more = info.pop('has_more', UNKNOWN)
        self.next = info.pop('next_page', UNKNOWN)
        
        self.messages = [Message(chat, msg_info, i + self.pos) for i, msg_info in enumerate(info.pop('messages', []))]
        
    def is_first(self) -> bool:
        """ Check if this is the first (oldest) page """
        return not self.more
    
    def is_last(self) -> bool:
        """ Check if this is the last (newest) page """
        return self.page == DEFAULT_LAST_MSG_PAGE
    
    def slide(self, slides: int) -> None:
        """ Slide to forward / backward pages """
        self.__init__(self.history, self.page + slides)

    def previous(self):
        """ Get the previous page """
        if self.is_first():
            raise errors.CAIError("This is the first page")
        return MessagePage(self.chat, self.page - 1)
        
    def next(self):
        """ Get the next page """
        if self.is_last():
            raise errors.CAIError("This is the last page")
        return MessagePage(self.chat, self.page + 1)

# Working...
class Chat:
    def exists(cai: Authenticated, external_id: str) -> bool:
        return cai.session.post(
            'chat/history/continue/',
            json={
                "character_external_id": external_id,
                "history_external_id": None
            }
        ).text.startswith(Chat.UNKNOWN_CHARACTER) 
    
    NO_CHAT_YET = "there is no history between user and character"
    UNKNOWN_CHARACTER = "no character found for"
    def __init__(self, cai: Authenticated, char: str|Character.Visible):
        self.cai = cai
        
        if isinstance(char, str):
            self._char = char
        else:
            self._char: str = char.external_id
            
        if not self._continue():
            self.active = self._new()
        else:
            self.active = True
            
        if self.active == False:
            raise errors.CAIError("Failed to join the chat")
        
        self.__final_init()
        
    def _continue(self) -> bool:
        info = self.cai.request(
            'chat/history/continue/',
            json={
                "character_external_id": self._char,
                "history_external_id": None
            },
            parse_output=False
        )
        if info == Chat.UNKNOWN_CHARACTER:
            raise errors.ServerError("Unknown character external id: \"{}\"")
        if info.startswith(Chat.NO_CHAT_YET):
            return False
        info = json.loads(json)
        
        self.created = parse_time(info.pop('created', UNKNOWN))
        self.last_interaction = parse_time(info.pop('last_interaction', UNKNOWN))
        
        self.history = History(self.cai, History.chat)
        self.history.load(info)
        
        self.greet = None
        
        return True
    
    def _new(self) -> bool:
        info = self.cai.request(
            'chat/history/create/',
            method='POST',
            json={
                'character_external_id': self._char
            }
        )

        self.created = parse_time(info.pop('created', UNKNOWN))
        self.last_interaction = parse_time(info.pop('last_interaction', UNKNOWN))
        
        self.history = History(self.cai, History.chat)
        self.history.load(info)
        
        self.greet = Message(self, info.pop('messages', [dict()])[0], 0)
        
        return info['status'] == "OK"
    
    def _load_info(self):
        info = self.cai.request(
            'chat/character/info/',
            method="POST",
            json={
                "external_id": self._char
            }
        )

    def __final_init(self):
        self.char = Character.Info(self.cai, self._char)
        delattr(self, '_char')
        self.first_page = MessagePage(self, DEFAULT_LAST_MSG_PAGE)
        self.voice_enabled = False
        self.remove = self.remove(self)
        
    def all_pages(self):
        if not self.active:
            raise errors.CAIError("The chat isn't active")
        it = copy.deepcopy(self.first_page)
        pages = [it]
        while not it.is_first():
            it = it.previous()
            pages.append(it)
        return pages
    
    def send(
            self, text: str, *, 
            ranking_method = "random", 
            staging = False,
            model_server_address = None,
            model_server_address_exp_chars = None,
            override_prefix = None,
            rooms_prefix_method = "",
            override_rank = None,
            rank_candidates = None,
            filter_candidates = None,
            unsanitized_characters = None,
            prefix_limit = None,
            prefix_token_limit = None,  
            stream_params = None,
            traffic_source = None,
            model_properties_version_keys = "",
            enable_tti = None,
            initial_timeout = None,
            insert_beginning = None,
            stream_every_n_steps = 16,
            is_proactive = False,
            image_rel_path = "",
            image_description = "",
            image_description_type = "",
            image_origin_type = "",
            seen_msg_uuids = [],
            retry_last_user_msg_uuid = None,
            num_candidates = 1,
            give_room_introductions = True,
            mock_response = False,
            **kwargs
        ):
        if not self.active:
            raise errors.CAIError("The chat isn't active")
        data = self.cai.request(
            'chat/streaming/', method="POST",
            split=True,
            json={
                "history_external_id": self.history.external_id,
                "character_external_id": self.char.external_id,
                "text": text,
                "tgt": self.char.username,
                "ranking_method": ranking_method,
                "staging": staging,
                "model_server_address": model_server_address,
                "model_server_address_exp_chars": model_server_address_exp_chars,
                "override_prefix": override_prefix,
                "rooms_prefix_method": rooms_prefix_method,
                "override_rank": override_rank,
                "rank_candidates": rank_candidates,
                "filter_candidates": filter_candidates,
                "unsanitized_characters": unsanitized_characters,
                "prefix_limit": prefix_limit,
                "prefix_token_limit": prefix_token_limit,
                "stream_params": stream_params,
                "traffic_source": traffic_source,
                "model_properties_version_keys": model_properties_version_keys,
                "enable_tti": enable_tti,
                "initial_timeout": initial_timeout,
                "insert_beginning": insert_beginning,
                "stream_every_n_steps": stream_every_n_steps,
                "is_proactive": is_proactive,
                "image_rel_path": image_rel_path,
                "image_description": image_description,
                "image_description_type": image_description_type,
                "image_origin_type": image_origin_type,
                "voice_enabled": self.voice_enabled,
                "parent_msg_uuid": None,
                "seen_msg_uuids": seen_msg_uuids,
                "retry_last_user_msg_uuid": retry_last_user_msg_uuid,
                "num_candidates": num_candidates,
                "give_room_introductions": give_room_introductions,
                "mock_response": mock_response,
                **kwargs
            }
        )

    class messages:
        """ Query messages """
        def __init__(self, chat):
            self.chat: Chat = chat

        def all(self):
            """ Returns all messages """
            it = copy.deepcopy(self.chat.first_page)
            messages = []

            messages.extend(it.messages)
            while not it.is_first():
                it.slide(-1)
                messages.extend(it.messages)

            return messages
        
        def range(self, end: int, start: int = 0):
            """
            Returns messages in range `start` to `end`, inclusively
            
            Parameters:
                end: the oldest message / index
                start: the newest message / index
                
            Note: messages are indexed from new to old
            """

            if start < 0:
                start = 0
            if start > end:
                start, end = end, start

            page = DEFAULT_LAST_MSG_PAGE - (start // 20)
            messages = []
            
            msg = self.history.get_messages(page)
            has_more = msg.get('has_more', False)
            msg = msg.get('messages', [])
            
            end -= start
            end += 1
        
            while end > 0 and len(msg) > 0:
                messages += [msg[i] for i in range(min(len(messages), end))]
                end -= len(min(len(messages), end))
                
                if not has_more:
                    break

                page -= 1

                msg = self.chat.history.get_messages(page)
                has_more = msg.get('has_more', False)
                msg = msg.get('messages', [])
                
            
            return msg

    class remove:
        """ Support message deleting """
        def __init__(self, chat):
            self.chat: Chat = chat
        
        def uuids(self, uuids: list[str]) -> bool:
            """ Delete all messages associated with given uuids """
            return self.cai.request(
                'chat/history/msgs/delete/',
                method='POST',
                json={
                    "history_id": self.history.external_id,
                    "uuids_to_delete": uuids
                }
            )['status'] == "OK"
            
        def all(self, mpr: int = 40) -> bool:
            """ Deletes all messages """
            if mpr < 0:
                return False

            success = True

            uuids = []
            queue_len = 0
            
            page = DEFAULT_LAST_MSG_PAGE
            messages = self.chat.history.get_messages(page)
            has_more = messages.get('has_more', False)
            messages = messages.get('messages', [])
            
            while len(messages) > 0:
                uuids += [messages[i].get('uuid') for i in range(min(len(messages), mpr - queue_len))]
                queue_len = len(uuids)
                
                if mpr == queue_len or queue_len == len(messages):
                    success &= self.uuids(uuids)
                    uuids = []
                    
                    page -= 1
                    
                    messages = self.chat.history.get_messages(page)
                    has_more = messages.get('has_more', False)
                    messages = messages.get('messages', [])
                    
                if not has_more:
                    break
            return success
        
        def range(self, end: int, start: int = 0, mpr: int = 40):
            """
            Removes messages in range `start` to `end`, inclusively
            
            Parameters:
                end: the oldest message / index
                start: the newest message / index
                mpr: messages per api request
                
            Note: messages are indexed from new to old
            """

            if start < 0:
                start = 0
            if start > end:
                start, end = end, start
                
            success = True
            
            uuids = []
            queue_len = 0

            page = DEFAULT_LAST_MSG_PAGE - (start // 20)
            
            messages = self.history.get_messages(page)
            has_more = messages.get('has_more', False)
            messages = messages.get('messages', [])
            
            end -= start
            end += 1
        
            while end > 0 and len(messages) > 0:
                uuids += [messages[i].get('uuid') for i in range(min(len(messages), end))]
                queue_len = len(uuids)
                
                end -= min(len(messages), end, mpr - queue_len)
                
                if mpr == queue_len or queue_len == len(messages) or queue_len == end:
                    success &= self.uuids(uuids[:mpr])
                    uuids = uuids[mpr:]
                    
                    if not has_more:
                        break
                    
                    page -= 1
                    
                    messages = self.chat.history.get_messages(page)
                    has_more = messages.get('has_more', False)
                    messages = messages.get('messages', [])
                    
            
            return success
        
        def messages(self, msgs: Collection[Message]):
            """ Removes messages by Message objects """
            return self.cai.request(
                'chat/history/msgs/delete/',
                method='POST',
                json={
                    "history_id": self.history.external_id,
                    "uuids_to_delete": [m.uuid for m in msgs]
                }
            )['status'] == "OK"
        
             
            
class Chat2:
    pass

class Client(Authenticated):
    """ A Character AI client """
    def __init__(self, token: str):
        """ Creates a new client """
        super().__init__(token=token)

    class User:
        """ Perform tasks related to users """
        def __init__(self, cai: CAI):
            self.cai = cai

        def self(self) -> User.Me:
            """ Get the current user """
            return User.Me(self.cai)
        
        def get_user_info(self, username: str) -> User.Other:
            """ Get user information """
            return User.Other(username, self.cai)
        
    class Post:
        """ Perform tasks related to posts """
        def __init__(self, cai: CAI):
            self.cai = cai

        def get_user_posts(self, username: str, *, page: int = 1, loads: int = 5) -> list[Post.UserPage]:
            """ Gets a user's posts """
            return [
                Post.UserPage(self.cai, info)
                for info in 
                self.cai.request(f'chat/posts/user/?username={username}&page={page}&posts_to_load={loads}/').pop('posts', [])
            ]
        
        def upload_chat(
            self, 
            external_id: str, 
            title: str, *,
            visibility: Visibility = Visibility.PUBLIC,
            message_range: tuple[int|int] = None,
        **kwargs):
            """ Uploads a chat (to feed)"""

            data = {
                'post_title': title,
                'subject_external_id': external_id,
                'post_visibility': visibility,
                **kwargs
            }
            if message_range != None:
                data['post_message_start'], data['post_message_end'] = message_range
            # Returns a json containing the post's external id
            return Post(self.cai, self.cai.request('chat/chat-post/create/', method="POST", data=data)['post']['external_id'])
        
        def get_topics(self):
            """ Get all topics """
            return [Topic(info=info) for info in self.cai.request('chat/topics/')['topics']]
        
    class Character:
        """ Perform tasks related to characters """
        def __init__(self, cai: CAI):
            self.cai = cai

        def get(self, external_id: str):
            """ Get control of this user's character """
            return Character.Character(self.cai, external_id)
        
        def info(self, external_id: str):
            """ Get character's information """
            return Character.Info(self.cai, external_id)
        
        def categories(self):
            """ Get all categories """
            return [Category(**info) for info in self.cai.request('chat/character/categories/')['categories']]
        
        def voices(self):
            """ Get all voices """
            return [Voice(**info) for info in self.cai.request('chat/character/voices/')['voices']]
        
    def user_api(self) -> User:
        """ Get the users manager """
        return Client.User(self)
    
    def post_api(self) -> Post:
        """ Get the posts manager """
        return Client.Post(self)
    
    def character_api(self) -> Character:
        """ Get the characters manager """
        return Client.Character(self)
        
