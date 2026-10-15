from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Lee el header "Authorization: Bearer <token>" y pone el candado en Swagger
bearer = HTTPBearer()

# Alias reutilizable en cualquier router protegido
Token = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]