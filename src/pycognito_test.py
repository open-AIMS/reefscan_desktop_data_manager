import boto3
import botocore
import requests
from pycognito import Cognito, AWSSRP
import base64
import hashlib
import hmac

from pycognito.utils import RequestsSrpAuth


def get_secret_hash(username, client_id, client_secret):
    message = username + client_id
    dig = hmac.new(bytearray(client_secret, "utf-8"), msg=message.encode('UTF-8'),
    digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


region = 'ap-southeast-2'
user_pool_id = 'ap-southeast-2_Bfy3rIq09'
client_id = '61kfuuandb828hnknv4psc80u3'
client_secret = '1val73g9dl1reioa97i0e88pkn77b776omj5j09t60kb6kr9ntfn'
user_name = 'gcoleman72@gmail.com'
password = 'AylaAyla12.'
auth_data = {'USERNAME': user_name, 'PASSWORD': password,
             'SECRET_HASH': get_secret_hash(user_name, client_id, client_secret)}
account_id = '192162795848'
provider_name = 'cognito-idp.ap-southeast-2.amazonaws.com/ap-southeast-2_Bfy3rIq09'
cognito_uri = 'https://reefscan.auth.ap-southeast-2.amazoncognito.com'
identity_pool_id = 'ap-southeast-2:bff88b28-1ed3-4f1f-aa5b-2f89ce751ff1'


u = Cognito(user_pool_id,client_id,username=user_name, client_secret=client_secret)
u.authenticate(password=password)
u.verify_tokens()
u.check_token()

print (u.access_token)
client = u.client
print (client)
print(u.access_claims)
auth = RequestsSrpAuth(
    cognito=u
)

print (auth)

response = requests.get('https://xmg5fq67x3.execute-api.ap-southeast-2.amazonaws.com/prod/reefscan/api/upload?file_name=greg', auth=auth)
print(response.text)

aws = AWSSRP(username=user_name, password=password, pool_id=user_pool_id,
             client_id=client_id, client_secret=client_secret, pool_region=region)
tokens = aws.authenticate_user()
print(tokens)