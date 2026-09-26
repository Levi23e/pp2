import json

# Открываем JSON-файл
with open("sample-data.json", "r") as file:
    data = json.load(file)

# Выводим заголовок таблицы
print("Interface Status")
print("=" * 80)
print(f"{'DN':<50} {'Description':<20} {'Speed':<7} {'MTU':<6}")
print(f"{'-'*50} {'-'*20} {'-'*7} {'-'*6}")

# Проходим по всем интерфейсам и выводим их атрибуты
for item in data['imdata']:
    attr = item['l1PhysIf']['attributes']
    dn = attr.get('dn', '')
    descr = attr.get('descr', '')
    speed = attr.get('speed', '')
    mtu = attr.get('mtu', '')
    
    print(f"{dn:<50} {descr:<20} {speed:<7} {mtu:<6}")
