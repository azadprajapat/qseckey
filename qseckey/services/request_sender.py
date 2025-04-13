import requests

class RequestSender:
    def __init__(self, base_url):
        self.base_url = base_url


    def get(self, endpoint, params=None, headers=None):
        """Sends a GET request to the specified endpoint."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response  # Return JSON response
        except requests.exceptions.RequestException as e:
            print (e)
            return None

    def post(self, endpoint, data=None, json=None, headers=None):
        """Sends a POST request to the specified endpoint."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, data=data, json=json, headers=headers)
            response.raise_for_status()
            return response 
        except requests.exceptions.RequestException as e:
            print(e)
            return None