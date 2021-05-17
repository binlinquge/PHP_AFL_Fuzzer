def getParamName(condition):
  param=[]
  while "_GET[" in condition:
    start = condition.find("_GET[")+5
    end = condition.find("]", start)
    param.append(condition[start:end])
    condition = condition[end:]
  return param

f = open("/var/www/html/CE-Phoenix-master/contact_us.php", "r");
source_code = f.readlines()
f.close()

param=[]

for i in range(len(source_code)):
  code = source_code[i]
  condition=""
  if "if (" in code:
    start = code.find("(", code.find("if"))
    end = start
    q = 1
    l = 1
    while q!=0:
      end+=1
      if end==len(code):
        print(condition)
        condition = condition+code[start:]
        code = source_code[i+l]
        l+=1
        start = 0
        end = 0
      if code[end]=="(":
        q+=1
      if code[end]==")":
        q-=1
    condition = condition+code[start:end+1]
    print(condition)

    param.extend(getParamName(condition))
param=list(set(param))
print(param)
