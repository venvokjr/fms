import requests

API_URL = 'https://messaging-service.co.tz/api/sms/v1/balance'

headers = {
        'Authorization': 'Basic VmVudm9ranI6R2FtZWwwZnQ=',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

res = requests.get(API_URL,headers=headers)
print(res.json().get('sms_balance'))