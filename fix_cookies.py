import json

with open('session.json', 'r') as f:
    data = json.load(f)

# Fix sameSite values
for cookie in data.get('cookies', []):
    if 'sameSite' in cookie:
        if cookie['sameSite'] in ['unspecified', 'no_restriction', 'None']:
            cookie['sameSite'] = 'None'
        elif cookie['sameSite'] == 'strict':
            cookie['sameSite'] = 'Strict'
        elif cookie['sameSite'] == 'lax':
            cookie['sameSite'] = 'Lax'
        else:
            cookie['sameSite'] = 'None'

with open('session.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Fixed sameSite values in session.json")
