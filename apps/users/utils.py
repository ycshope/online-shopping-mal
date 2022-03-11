from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo import settings

EXPRIRES_IN = 300  #openid最大过期时间
# import time

def generic_email_verify_token(userid):
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=EXPRIRES_IN)
    # s = Serializer(secret_key=SECRET_KEY, expires_in=1)
    access_token = s.dumps({'userid': userid})
    return access_token.decode()


def decrypt_userid(token):
    # s = Serializer(secret_key=SECRET_KEY, expires_in=60)
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=EXPRIRES_IN)
    try:
        result = s.loads(token)
    except Exception:
        return None
    else:
        return result.get('userid')


if __name__ == "__main__":
    context = encrypt_userid('123456')
    print(context)
    # time.sleep(1.9)
    print(decrypt_userid(context))
