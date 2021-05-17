import json

file_name = "/home/user/Downloads/satpaths_all.json"

f = open(file_name, "r")
paths = json.loads(f.read())
f.close()

print(paths[0])
