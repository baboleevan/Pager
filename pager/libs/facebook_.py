import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from flask import request
from timezone import KST, now

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor 
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def parse_signed_request(signed_request, secret, expires_in=None):
    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))
    if data.get('algorithm').upper() != 'HMAC-SHA256':
        log.error('Unknown algorithm')
        return None
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        return None

    data['issued_at'] = \
        datetime.fromtimestamp(data['issued_at']).replace(tzinfo=KST)
    if expires_in:
        data['expires_at'] = data['issued_at'] + timedelta(seconds=expires_in)
        if now() > data['expires_at']:
            return None
    return data

def signed_request(secret):
    sign = request.form.get('signed_request', None)
    if sign:
        return parse_signed_request(sign, secret)
    return
