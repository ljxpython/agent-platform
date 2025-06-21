# 调试时使用
# import os
# import sys
# from pathlib import Path
# print(str(Path(__file__).parent.parent.parent))
# sys.path.append(str(Path(__file__).parent.pareot.parent))

import jwt
from app.conf.config import settings
from app.schemas.login import JWTPayload


def create_access_token(*, data: JWTPayload):
    payload = data.model_dump().copy()
    print(payload)
    encoded_jwt = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


if __name__ == "__main__":

    resp = create_access_token(
        data=JWTPayload(
            user_id=1, username="admin", is_superuser=True, exp="2022-12-31 00:00:00"
        )
    )
    print(resp)
