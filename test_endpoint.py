import requests

# Test the endpoint
response = requests.get('http://127.0.0.1:5001/classteacher/teacher_streams/1')
print(f'Status code: {response.status_code}')
if response.status_code == 200:
    print(f'Response: {response.json()}')
else:
    print(f'Error: {response.text}')
