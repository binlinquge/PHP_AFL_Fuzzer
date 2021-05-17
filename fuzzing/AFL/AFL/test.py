import requests

def fuzzOnce(path, method, data):
  url = "http://"+path.replace("/var/www/html","localhost")
  if method == "GET":
    requests.get(url, params=data)
  elif method == "POST":
    r = requests.post(url, data=data)
    print(r.text)
  else:
    return -1
  return 0

data = {"test":"test"}
fuzzOnce("/var/www/html/schoolmate_small/ManageTeachers.php", "POST", data)
