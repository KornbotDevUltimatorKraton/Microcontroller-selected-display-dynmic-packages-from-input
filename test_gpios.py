import requests

url = "http://192.168.50.247:9058/get_component_gpios"
payload = {
    "email": "kornbot380@hotmail.com",
    "project_name": "Hexbot_design",
    "mcusdata": "STM32F303K8"
}

response = requests.post(url, json=payload)
print(response.json())
