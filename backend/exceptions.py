# 获取异常

class BusinessError(Exception):
    pass


class PermissionDenied(BusinessError):
    pass


class NotFound(BusinessError):
    pass