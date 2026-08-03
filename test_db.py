import requests
url = "http://192.168.50.247:5978/mcus_dbpath"
payload = {"email": "kornbot380@hotmail.com", "project_name": "Hexbot_design", "mcusdata": "STM32F401RET6"}
response = requests.post(url, json=payload)
print(response.status_code, "Length:", len(str(response.json())))
