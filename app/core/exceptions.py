from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Not found resource"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ForbiddenException(HTTPException):
    def __init__(self, detail: str = "Forbidden action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

class ConflictException(HTTPException):
    def __init__(self, detail: str = "Already exists resource"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)