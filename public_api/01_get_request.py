import requests

url = "https://jsonplaceholder.typicode.com/posts/1"
response = requests.get(url)
data = response.json() 
print(response.status_code)
#print(response.json())
#print(data['title'])



url1 = "https://jsonplaceholder.typicode.com/posts/1/users"
response1 = requests.get(url1)
data1 = response1.json() 
print(response1.status_code)
#print(response1.json())
print(data1[0]['name'])
print(data1[0] ['email'])
print(data1[0]['company']['name'])
print('-------------------------------')
for user in data1:
    print(user['name'])
    print(user['email'])
    print(user['company']['name'])
    print('-------------------------------')


