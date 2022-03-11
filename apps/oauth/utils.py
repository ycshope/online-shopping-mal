from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo import settings

EXPRIRES_IN = 300  #openid最大过期时间
# import time

# SECRET_KEY = 'django-insecure-=123456'


def encrypt_openid(openid):
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=EXPRIRES_IN)
    # s = Serializer(secret_key=SECRET_KEY, expires_in=1)
    access_token = s.dumps({'openid': openid})
    return access_token.decode()


def decrypt_openid(token):
    # s = Serializer(secret_key=SECRET_KEY, expires_in=60)
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=EXPRIRES_IN)
    try:
        result = s.loads(token)
    except Exception:
        return None
    else:
        return result.get('openid')


if __name__ == "__main__":
    context = encrypt_openid('123456')
    print(context)
    # time.sleep(1.9)
    print(decrypt_openid(context))
