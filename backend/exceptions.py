# backend/exceptions.py

class BusinessError(Exception):
    pass


class PermissionDenied(BusinessError):
    pass


class NotFound(BusinessError):
    pass