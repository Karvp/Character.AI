DEFAULT_ERROR_MSG = "Failed to perform action(s)!"


class CAIError(Exception):
    pass

class UnexpectedError(CAIError):
    pass

class ConnectionError(CAIError):
    pass    

class ValueError(CAIError):
    pass

class UserError(CAIError):
    pass

class PermissionError(CAIError):
    pass

class AuthError(CAIError):
    pass

class ServerError(CAIError):
    pass