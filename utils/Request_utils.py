import requests

def query_api(method, url, headers, params, json_payload, attempts = 1):
    try:
        attempt = 0
        res = None
        while attempt < attempts:
            attempt = attempt + 1
            if method == 'get':
                res = requests.get(url, params=params, headers=headers, json=json_payload)
            elif method =='post':
                res = requests.post(url, params=params, headers=headers, json=json_payload)
            else:
                raise Exception('Unexpected method.')
            if res.status_code == 200:
                break
        
        return { 'code': res.status_code, 'json' : res.json() }
    
    except Exception as e:
        print('Error with request: method: ', method, ', url: ', url, ', headers: ', headers, ', params: ', params, ', json_payload: ', json_payload)
        print('Error: ', str(e))
        return { 'code': res.status_code, 'json' : None, 'text': res.text }