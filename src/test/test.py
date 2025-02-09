import requests

citydic = {
    "name": "",
    "plz": 0,
}
cities = list()

citydic.update({"name": "test"})
citydic.update({"plz": 12345})

cities.append(citydic)
print(cities)
citydic.update({"name": "test2"})
citydic.update({"plz": 12345})
cities.append(citydic)

print(cities)
