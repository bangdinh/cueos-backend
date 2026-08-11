import uuid, jwt
ACTIVE_USER_SESSIONS = {}
user_id = 1
sid = str(uuid.uuid4())
ACTIVE_USER_SESSIONS[user_id] = sid
payload = {'user_id': user_id, 'sid': sid}
encoded = jwt.encode(payload, 'secret', algorithm='HS256')
decoded = jwt.decode(encoded, 'secret', algorithms=['HS256'])
print(f"Decoded user_id: {decoded.get('user_id')}, type: {type(decoded.get('user_id'))}")
print(f"Active sid: {ACTIVE_USER_SESSIONS.get(decoded.get('user_id'))}")
