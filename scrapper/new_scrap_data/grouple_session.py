import requests
from requests.auth import HTTPProxyAuth


class GroupleSession:
    def __init__(self, proxy_data):
        self.session = requests.Session()
        self.session.trust_env = False
        
        auth = proxy_data['login'] + ':' + proxy_data['password']
        proxy = auth + '@' + proxy_data['address'] + ':' + proxy_data['port']
        self.proxy = {'http': 'http://%s/' % proxy,
                      'https':'https://%s/' % proxy}
        
        url = 'https://grouple.co/login/authenticate'
        payload = {'username': 'ARQtty', 'password': '28dog28DOG'}
        self.session.post(url, data=payload, proxies=self.proxy)
    
    
    def load_user(self, url):
        res = self.session.get(url, proxies=self.proxy)
        return res