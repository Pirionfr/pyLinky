
class PyLinkyException(Exception):
    pass

class PyLinkyAccessException(PyLinkyException):
    pass

class PyLinkyEnedisException(PyLinkyException):
    pass

class PyLinkyMaintenanceException(PyLinkyException):
    pass

class PyLinkyWrongLoginException(PyLinkyException):
    pass
