import copy
import time
import pymysql
from py2neo import Graph
import json
import requests
from Gen_input import Gen_input
import os

#mysql "localhost", "fuzz", "User_123", "fuzz"
db = pymysql.connect(host="localhost", port=3306, user="fuzz", passwd="User_123", db="fuzz")
#neo4j neo4j neo
#graph = Graph(auth=('neo4j', 'user'))
graph = Graph(auth=('neo4j', 'neo'))

#Write the original code to the file so that the file will not be modified after any instrument
def revertFile(code, file):
    f = open(file, "w")
    for line in code:
        f.write(line)
    f.close()

#Check file to see if the file has been instrumented. If so, revert it to origianl code first
def checkFile(file, offsetA):
    f = open(file, "r")
    code = f.readlines()
    f.close()
    if "final class FuzzingContext {" in code[1]:
        revertFile(code[offsetA:], file)
        print("File was instrumented")
    return 1

#Refresh database connection to make sure the data we get is up to date
def dbRefresh(db):
  try:
    db.close()
  except:
    pass
  db = pymysql.connect(host="localhost", port=3306, user="fuzz", passwd="User_123", db="fuzz")
  return db

#Find the last condiiton that is before 'stop_lineno'
def findLastCondition(stop_lineno, source_code):
  stop_condition = -1
  conditions={}
  for index in range(stop_lineno):
      index = stop_lineno-index
      if "FuzzingContext::traceBlock(" in source_code[index]:
          conditions, temp2 = getConditions(source_code[index], index)
          stop_condition = temp2[0]
          break
  return stop_condition, conditions

#Find the condition that stops the target file from executing
def findStopCondition(conditions_ids, ex_condition):
  stop_condition = -1
  stop_con_line = -1
  for index in range(len(conditions_ids)-1):
      if (conditions_ids[index] in ex_condition) and (conditions_ids[index+1] not in ex_condition):
          stop_condition = conditions_ids[index]
          break
  return stop_condition, stop_con_line

#Get all the conditions between stop_lineno and lineno
def getConditionsBtwLine(lineno, stop_lineno, source_code):
  conditions = {}
  conditions_ids = []
  for index in range(stop_lineno, lineno):
      start = 0
      while "FuzzingContext::traceBlock(" in source_code[index][start:]:
          id = source_code[index][source_code[index].find("FuzzingContext::traceBlock(", start)+27: source_code[index].find(",", start)]
          start = source_code[index].find(",", start)
          end = start
          while source_code[index][end] not in ['|', '&', ')']:
              end += 1
          con = source_code[index][start:end]
          conditions[id] = [con, index+1]
          conditions_ids.append(id)
          start = end+1
  return conditions, conditions_ids

#Transfer lineno to block ID
def linenoToBlockID(lineno, source_code):
  target_blockID = -1
  for index in range(lineno):
      index = lineno - index
      if "$___key" in source_code[index]:
          start = source_code[index].find("$___key = ")+10
          target_blockID = int(source_code[index][start:source_code[index].find(";", start)])
          break
  return target_blockID

#print all the variable that is depend on the stop condition. The right one of them need to be reached in order to reach the target.
def printDp(i, dp_lineno, filename, source_code, ex_block, temp_conditions, nodeids=[0,0,0,0]):
  blockID = linenoToBlockID(dp_lineno, source_code)
  #print(blockID)
  if_reached = "not reached"
  if blockID in ex_block:
    if_reached = "reached"
  print("\t",i, "(", nodeids[3],"->",nodeids[0], "):",if_reached, " lineno: ", dp_lineno," in file: ", filename ," : ", source_code[dp_lineno-1], end="")
  #print("\tConditions before this dependence:\n\t")

  printed = []
  for condition in temp_conditions:
    if temp_conditions[condition][1]-1 not in printed:
      #print(source_code[temp_conditions[condition][1]-1])
      printed.append(temp_conditions[condition][1]-1)

  #if if_reached == "reached":
  temp_conditions["blockID"] = blockID
  return if_reached, temp_conditions

#Find the variables that is depend on the nodes in line 'stop_con_line' of file 'fileid'
def findLastDp(stop_con_line, fileid, conditions, stop_condition, graph):
  last_dps = []
  query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"})-[:PARENT_OF*]->(a) where \""+str(conditions[stop_condition][0]).replace("\\","\\\\").replace("\"", "\\\"").replace("\'","\\\'")+"\" CONTAINS a.code with n match (n)<-[:REACHES]-(b) return b.id, b.lineno, b.fileid, n.id"
  #print(query)
  result = graph.run(query).data()
  if not result:
    query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"})-[:PARENT_OF*]->(a) where \""+str(conditions[stop_condition][0]).replace("\\","\\\\").replace("\"", "\\\"").replace("\'","\\\'")+"\" CONTAINS a.code with n match (n)<-[:REACHES*2]-(b) return b.id, b.lineno, b.fileid, n.id"
    result = graph.run(query).data()
    if not result:
      query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"})-[:PARENT_OF*]->(a) where \""+str(conditions[stop_condition][0]).replace("\\","\\\\").replace("\"", "\\\"").replace("\'","\\\'")+"\" CONTAINS a.code with n match (n)<-[:REACHES*3]-(b) return b.id, b.lineno, b.fileid, n.id"
      result = graph.run(query).data()
  for r in result:
      if ([r["b.id"], r["b.lineno"], r["b.fileid"], r["n.id"]] not in last_dps):
        last_dps.append([r["b.id"], r["b.lineno"], r["b.fileid"], r["n.id"]])
  return last_dps

#From the 'stop_con_line', see if we can find any superglobal varialbes that we can fuzz directly. If not, we probably need to solve a sub-question first
def findToBeFuzzed(stop_con_line, fileid, conditions, stop_condition, graph):
  toBeFuzzed = []
  query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"}) where n.code=\"_GET\" or n.code=\"_POST\" return n.id"
  #print(query)
  result = graph.run(query).data()
  for r in result:
      toBeFuzzed.append(r["n.id"])
  if not toBeFuzzed:
      query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"})-[:PARENT_OF*]->(a) where \""+str(conditions[stop_condition][0]).replace("\\","\\\\").replace("\"", "\\\"").replace("\'","\\\'")+"\" CONTAINS a.code with n match (n)<-[:REACHES]-(b) with b match (b)-[:PARENT_OF*]->(c) where c.code=\"_GET\" or c.code=\"_POST\" return c.id"
      #print(query)
      result = graph.run(query).data()
      for r in result:
          toBeFuzzed.append(r["c.id"])
  if not toBeFuzzed:
      query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"})-[:PARENT_OF*]->(a) where \""+str(conditions[stop_condition][0]).replace("\\","\\\\").replace("\"", "\\\"").replace("\'","\\\'")+"\" CONTAINS a.code with n match (n)<-[:REACHES*2]-(b) with b match (b)-[:PARENT_OF*]->(c) where c.code=\"_GET\" or c.code=\"_POST\" return c.id"
      #print(query)
      result = graph.run(query).data()
      for r in result:
          toBeFuzzed.append(r["c.id"])
  if not toBeFuzzed:
      query = "match (n {lineno:"+str(stop_con_line)+", fileid:"+str(fileid)+"})-[:PARENT_OF*]->(a) where \""+str(conditions[stop_condition][0]).replace("\\","\\\\").replace("\"", "\\\"").replace("\'","\\\'")+"\" CONTAINS a.code with n match (n)<-[:REACHES*3]-(b) with b match (b)-[:PARENT_OF*]->(c) where c.code=\"_GET\" or c.code=\"_POST\" return c.id"
      #print(query)
      result = graph.run(query).data()
      for r in result:
          toBeFuzzed.append(r["c.id"])
  return toBeFuzzed

#Use fileid to find the name of the file
def getFileName(file_ID, graph):
    query = "MATCH (n {id:"+str(file_ID)+"}) return n.name"
    result = graph.run(query).data()
    return result[0]["n.name"]

#Get the lineno of a node
def getNodeLineno(node_ID, graph):
    query = "MATCH (n {id:"+str(node_ID)+"}) return n.lineno, n.fileid"
    result = graph.run(query).data()
    return result[0]["n.lineno"], result[0]["n.fileid"]

#Given a line of code, find out the condition contained in this line by using string matching.
def getConditions(line, index):
    start = 0
    conditions = {}
    conditions_ids = []
    while "FuzzingContext::traceBlock(" in line[start:]:
        id = line[line.find("FuzzingContext::traceBlock(", start)+27: line.find(",", start)]
        start = line.find(",", start)
        end = start
        while line[end] not in ['|', '&', ')']:
            end += 1
        con = line[start:end]
        conditions[id] = [con,index+1]
        conditions_ids.append(id)
        start = end+1
    return conditions, conditions_ids

#Send an HTTP request to get some initial trace info
def fuzzOnce(path, method, data):
  print("Fuzz once: ", path, method, data)
  url = "http://"+path.replace("/var/www/html","localhost")
  if method == "GET":
    requests.get(url, params=data)
  elif method == "POST":
    requests.post(url, data=data)
  else:
    return -1
  return 0

#Get the total records in database
def getTotalRecords(db):
  result = -1
  query = "SELECT COUNT(*) FROM cephoenix"
  try:
    cursor = db.cursor()
    cursor.execute(query)
    result = cursor.fetchall()[0][0]
    cursor.close()
  except:
    result = -1

  if result==-1:
    db = dbRefresh(db)
    cursor = db.cursor()
    cursor.execute(query)
    result = cursor.fetchall()[0][0]
    cursor.close()
  return result, db

#Get the trace infomation in the database
def getTraceInfo(id, db):
  result = []
  query = "SELECT ex_block, ex_condition FROM cephoenix WHERE id="+str(id)

  cursor = db.cursor()
  cursor.execute(query)
  result = list(cursor.fetchall())
  cursor.close()

  if not result:
    time.sleep(1.0)
    db = dbRefresh(db)
    cursor = db.cursor()
    cursor.execute(query)
    result = list(cursor.fetchall())
    cursor.close()
    if not result:
      return -1,-1,db

  return json.loads("["+result[0][0][:-1]+"]"), json.loads("["+result[0][1][:-1]+"]"),db

#When we start fuzzing a target file, we need to insert some code at the beginning of the file in order to make it running
def instrumentTargetFile(path, file_to_fuzz="N", fuzz_index=0, message="N"):
  addInfo = """<?php
final class FuzzingContext {
    public static $prevBlock = 0;
    public static $edges = [];
    public static $condition = [];

    public static function reset() {
        self::$prevBlock = 0;
        self::$edges = [];
        self::$condition = [];
    }

    public static function traceBlock($blockIndex, $returnValue) {
        $key = $blockIndex;
        self::$condition[$key] = (self::$condition[$key] ?? 0) + 1;
        return $returnValue;
    }
}

function WriteTraceToFile(){
  $temp = "";
  $temp2 = "";

    foreach (FuzzingContext::$edges as $key => $value){
      $temp = $temp.strval($key).",";
    }
    foreach (fuzzingContext::$condition as $key=> $value){
      $temp2 = $temp2.strval($key).",";
    }

  $conn = new mysqli("localhost", "fuzz", "User_123", "fuzz");
  $sql = "INSERT INTO cephoenix (file_name, ex_block, ex_condition, input) VALUES ('".basename(strtok($_SERVER['REQUEST_URI'], '?'))."','".$temp."','".$temp2."','".json_encode($_GET)."')";
  if ($conn->query($sql)===TRUE){
    echo "success to write to mysql";
  }else{
    echo $sql;
    echo "fail to write into mysql:".$conn->error;
  }
  $conn->close();
}
register_shutdown_function("WriteTraceToFile");
?>
"""
  f = open(path, "r")
  code = f.readlines()
  f.close()
  f = open(path, "w")
  f.write(addInfo)

  start_line = 0
  if code[1].find("class FuzzingContext")!=-1:
      start_line = 42

  if file_to_fuzz!="N" and message == "N":
    f2 = open(file_to_fuzz, "r")
    fuzzCode = f2.readlines()
    f2.close()
    for i in range(len(fuzzCode)):
      if i==fuzz_index:
        break
      f.write(fuzzCode[i])
    f.write("?>\n")

  for line in code[start_line:]:
    f.write(line)
  f.close()
  return code

#replace the target file with original code
def restoreTargetFile(code, path):
  f = open(path, "w")
  for line in code:
    f.write(line)
  f.close()

#After we find some variables that depends on the stop conditon, we need to do some analysis to it. There are two cases:
#1. The variable is in the target file
#2. The variable is in another file that different than the target file
#If there are some variables that are reached, it means they shouldn't be reached otherwise the target line should already been reached
#If there are no variables that are reached, it means we need to do something to make some of them been reached. Untill we find the correct one that need to be reached
def analysisDPs(last_dps, fileid, offsetA, source_code, file_path, ex_block, graph):
    conditions_to_store = []
    result_condition = []
    condition_code = ""
    ans = False
    for i in range(len(last_dps)):
      temp_conditions = {}
      if last_dps[i][2] == fileid:
          temp_condition, temp_conditions = findLastCondition(last_dps[i][1]+offsetA, source_code)
          if_reached, temp_condition = printDp(i, last_dps[i][1]+offsetA, file_path, source_code, ex_block, temp_conditions, last_dps[i])
          if if_reached=="reached" and not result_condition:
              added = []
              for condition in temp_condition:
                  if isinstance(temp_condition[condition], list) and temp_condition[condition][1]-1 not in added:
                      condition_code+=source_code[temp_condition[condition][1]-1]
                      added.append(temp_condition[condition][1]-1)
              result_condition= copy.deepcopy(temp_condition)
              ans = True
              break
      else:
          temp_file_path = getFileName(last_dps[i][2],graph)
          temp_file_path = temp_file_path.replace("cephoenix", "CE-Phoenix-master")

          f = open(temp_file_path, "r")
          temp_source_code = f.readlines()
          f.close()

          temp_condition, temp_conditions = findLastCondition(last_dps[i][1], temp_source_code)
          if_reached, temp_condition = printDp(i, last_dps[i][1], temp_file_path, temp_source_code, ex_block, temp_conditions, last_dps[i])
          if if_reached=="reached" and not result_condition:
              added = []
              for condition in temp_condition:
                  if isinstance(temp_condition[condition], list) and temp_condition[condition][1]-1 not in added:
                      condition_code+=source_code[temp_condition[condition][1]-1]
                      added.append(temp_condition[condition][1]-1)
              result_condition = copy.deepcopy(temp_condition)
              ans=True
              break
      conditions_to_store.append(temp_conditions)
    if not ans and last_dps:
      i = int(input("please choose an intermediate point to reach from above:"))
      temp_conditions = {}
      if last_dps[i][2] == fileid:
          temp_condition, temp_conditions = findLastCondition(last_dps[i][1]+offsetA, source_code)
          if_reached, temp_condition = printDp(i, last_dps[i][1]+offsetA, file_path, source_code, ex_block, temp_conditions, last_dps[i])
          if not result_condition:
              added = []
              for condition in temp_condition:
                  if isinstance(temp_condition[condition], list) and temp_condition[condition][1]-1 not in added:
                      condition_code+=source_code[temp_condition[condition][1]-1]
                      added.append(temp_condition[condition][1]-1)
              result_condition= copy.deepcopy(temp_condition)
              ans = True
              #break
      #print(last_dps[choice])
    print(conditions_to_store, result_condition, condition_code)
    return conditions_to_store, result_condition, condition_code

#Save some info about the conditions we met. For test reason only
def restoreCondition(conditions, stop_condition, conditions_to_store):
  choice = int(input("logging conditions:(0/1):"))
  #print("If record conditions:(0/1) ", choice)
  if choice==1:
    f = open("conditions.log", "a")
    f.write("Stop condition:")
    f.write(str(conditions[stop_condition])+"\n")
    f.write("Next to solve:")
    f.write(str(conditions_to_store)+"\n\n")
    f.close()

#Get the name of the parameter given the node id of the parameter
def getParamName(nodeid):
  query = "match (n {id:"+str(nodeid+1)+"}) return n.code, n.type"
  result = graph.run(query).data()
  return result[0]["n.code"], result[0]["n.type"]

#Just a format transfer for the input
def prepareData(input):
  result = {}
  for key in input:
    result[key] = input[key][0]
  return result

#This function uses other two child funciton to find and solve the dependences
def findSolveDPs(stop_con_line, fileid, conditions, stop_condition, offsetA, source_code, file_path, ex_block, target_blockID, graph):
    #print(ex_block)
    last_dps = findLastDp(stop_con_line, fileid, conditions, stop_condition, graph)
    #print(last_dps)
    conditions_to_store, result_condition, condition_code = analysisDPs(last_dps, fileid, offsetA, source_code, file_path, ex_block, graph)
    if result_condition:
        print("We need to unsat these conditions:")
        print(condition_code)
        return "subQ", file_path, result_condition, db
    else:
        print("We did not find any intermediate point to unreach.. we can do nothing to these cases yet")
        return -1, file_path, target_blockID, db

#If the page was crashed, it might be that there are some input values that didn't been initialized. Here, we add all possible parameter name to the input array
def expendInputs(inputs, original_code):
    for line in original_code:
        flag = "N"
        paramValue = "default"
        paramType = "String"
        if "_GET[" in line:
            flag = "GET"
            start_index = line.find("_GET[")
            while start_index!=-1:
                start_index += 5
                end_index = line.find("]", start_index)
                paramName = line[start_index:end_index]
                inputs[paramName] = [paramValue, paramType, flag]
                start_index = line.find("_GET[", end_index)
        if "_POST[" in line:
            flag = "POST"
            start_index = line.find("_POST[")
            while start_index!=-1:
                start_index += 6
                end_index = line.find("]", start_index)
                paramName = line[start_index:end_index]
                inputs[paramName] = [paramValue, paramType, flag]
                start_index = line.find("_POST[", end_index)
    return inputs

#Extract the file name from a path
def extractName(file_path):
    ii = 0
    for i in range(len(file_path)):
        ii = len(file_path)-1-i
        if file_path[ii] == "/":
            break
    if ii==0:
        return file_path
    return file_path[ii+1:]

#Find out all files that are including the target file
def includedBy(file_path):
    dir = input("What's the root dir of app?\n")
    filename = extractName(file_path)

    filepath = [dir]
    fuzz_index = 0
    while filepath:
        path = filepath.pop(0)
        path = path+"/"
        # print("current path: " + path)
        raw = os.listdir(path)
        files = []
        for x in raw:
            if os.path.isdir(path + x):
                filepath.append(path + x)
            else:
                if x[-4:] == ".php":
                    files.append(path + x)

        for filename2 in files:
            print("Checked ", filename2, " for require(",filename,")")
            f = open(filename2, "r")
            code = f.readlines()
            f.close()
            for i in range(len(code)):
                line = code[i]
                if "require" in line and filename in line:
                    return filename2, i
    return "NN", 0

#This is the main funciton of this script. It tries to find out the next parameter to fuzz recursively.
#1.It finds out the stop line
#2.It finds out the conditon that makes the execution stop(preventing reaching the target line)
#3.It finds out the parameter that we can fuzz to potentially solve the problem.
#4.Or it decides to reach another target line first before we can reach the real target line
def nextToFuzz(target_nodeID, db, graph, inputs={}, offsetA=42, method="GET", message="N", file_to_fuzz="N", fuzz_index=0):
  #print("\nWe are trying to reach target node: ", target_nodeID)
  #print("Getting some basic info about the target...\n")
  print("inputs we have:", inputs)
  print("HTTP method:", method)
  #get total records in mysql
  time.sleep(1)
  db = dbRefresh(db)
  try:
    total_records,db = getTotalRecords(db)
  except:
    db = dbRefresh(db)
    total_records,db = getTotalRecords(db)

  print("Total trace info in DB: ",total_records)

  #sink node of a sat path
  print("Target node: ",target_nodeID)

  #get line number and file id of the target node (sink node in demo)
  lineno, fileid = getNodeLineno(target_nodeID, graph)
  offsetA += fuzz_index

  lineno += offsetA #add the line numbers of add info on top of file
  print("Target lineno: ", lineno)

  #get file name (full path)
  file_path = getFileName(fileid, graph)

  #for cephoenix, because the app name in neo4j is different from the file name in /var/www/html, we change it
  file_path = file_path.replace("cephoenix", "CE-Phoenix-master")
  file_path = file_path.replace("schoolmate", "schoolmate_small")
  print("Target file: ", file_path)

  #add instrument code tops to target file
  #checkFile(file_path, offsetA)
  original_code = instrumentTargetFile(file_path, file_to_fuzz, fuzz_index, message)

  #fuzz once to get ex_block and ex_condition
  fuzz_data = prepareData(inputs)
  fuzzOnce(file_path, method, fuzz_data)
  total_records+=1
  db = dbRefresh(db)
  ex_block, ex_condition, db = getTraceInfo(total_records, db)
  #print(ex_block)
  if ex_block == -1:
    print("Error: No trace was found in DB, this might becuase the page was crashed")
    #restoreTargetFile(original_code, file_path)
    result = (-1, file_path, -1, db)
    if message=="N":
        inputs = expendInputs(inputs, original_code)
        #restoreTargetFile(original_code, file_path)
        if file_to_fuzz != "N":
            result =  nextToFuzz(target_nodeID, db, graph, inputs, offsetA, "GET", "TRY_AGAIN", file_to_fuzz, fuzz_index)
        else:
            result =  nextToFuzz(target_nodeID, db, graph, inputs, offsetA, "GET", "TRY_AGAIN")
        #restoreTargetFile(original_code, file_path)
    if message == "TRY_AGAIN":
        #restoreTargetFile(original_code, file_path)
        if file_to_fuzz != "N":
            result =  nextToFuzz(target_nodeID, db, graph, inputs, offsetA, "POST", "RETURN", file_to_fuzz, fuzz_index)
        else:
            result =  nextToFuzz(target_nodeID, db, graph, inputs, offsetA, "POST", "RETURN")
    if message == "RETURN" and method == "POST":
        #fuzz_index = 0
        if file_to_fuzz != "N":
            print("Last file to fuzz:", file_to_fuzz, fuzz_index)
            file_to_fuzz, fuzz_index  = includedBy(file_to_fuzz)
            print("New file to fuzz:", file_to_fuzz, fuzz_index)
            if file_to_fuzz == "NN":
                print("Did not find any file \"require\" the target file as well.")
            else:
                result = nextToFuzz(target_nodeID, db, graph, inputs, offsetA, "GET", "N", file_to_fuzz, fuzz_index)
        else:
            file_to_fuzz, fuzz_index = includedBy(file_path)
            print("File to fuzz:", file_to_fuzz, fuzz_index)
            if file_to_fuzz == "NN":
                print("Did not find any file \"require\" the target file as well.")
            else:
                result = nextToFuzz(target_nodeID, db, graph, inputs, offsetA, "GET", "N", file_to_fuzz, fuzz_index)
    restoreTargetFile(original_code, file_path)
    return result
    #return -1, file_path, -1, db
  #get content of the target file
  f = open(file_path, "r")
  source_code = f.readlines()
  f.close()

  #get the target block ID
  target_blockID = linenoToBlockID(lineno, source_code)
  if target_blockID == -1:
      print("Error finding the target block ID. The target may be already reached or the file may not contain any block")
      restoreTargetFile(original_code, file_path)
      return -1, file_path, -1, db
  print("Target blockID: ", target_blockID)

  #if the target has been reached already, tell it
  if target_blockID in ex_block:
    print("the target block has been reached")
    print("The final input we used is:", inputs,"\n")
    restoreTargetFile(original_code, file_path)
    return -1, file_path, target_blockID, db

  #get most recent ex_block and ex_condition, this should be from AFL
  #print("executed blocks:(passed from AFL): ", ex_block)
  #print("executed conditions:(passed from AFL): ", ex_condition)

  #find the first unsat/sat condition that prevent us from reaching target block
  #print("\nfinding the first unsat/sat condition that prevent us from reaching target block...")
  ##1. find the executed block that right before the target block
  stop_block = -1
  stop_lineno = -1

  for index in range(lineno):
      if target_blockID-index in ex_block:
          stop_block = target_blockID-index
          stop_lineno = stop_block & (2**32-1)
          stop_lineno+=offsetA
          break

  if stop_block == -1:
      print("no block was executed, we can't solve the problem accurately now.")
      #if there is no block ahead, check if there is any conditions first
      stop_condition, conditions = findLastCondition(lineno, source_code)
      print("The condition need to go pass: ", conditions[stop_condition])
      if stop_condition != -1:
        stop_con_line = conditions[stop_condition][1]-offsetA
        #last_dps = findLastDp(stop_con_line, fileid, conditions, stop_condition, graph)
        print("Trying to find the dependence of the condition...")
        toBeFuzzed = findToBeFuzzed(stop_con_line, fileid, conditions, stop_condition, graph)
        if toBeFuzzed:
            restoreTargetFile(original_code, file_path)
            return toBeFuzzed, file_path, target_blockID, db
        else:
            print("Did not find global variables that depended by the condition, we need to solve a sub-question to get out from the wrong branch")
            restoreTargetFile(original_code, file_path)
            #restoreCondition(conditions, stop_condition, conditions_to_store)
            return findSolveDPs(stop_con_line, fileid, conditions, stop_condition, offsetA, source_code, file_path, ex_block, target_blockID, graph)

            #last_dps = findLastDp(stop_con_line, fileid, conditions, stop_condition, graph)
            #conditions_to_store, result_condition, condition_code = analysisDPs(last_dps, fileid, offsetA, source_code, file_path, ex_block, graph)
            #restoreTargetFile(original_code, file_path)
            #restoreCondition(conditions, stop_condition, conditions_to_store)
      else:
        restoreTargetFile(original_code, file_path)
        print("Error: did not find a stop block, the target page may crashed")
      return -1, file_path, target_blockID, db
  print("Stop block: ",stop_block)
  print("\nExecution stops at line number: ",stop_lineno)

  ##2. find all conditions between target block and stopped block
  conditions, conditions_ids = getConditionsBtwLine(lineno, stop_lineno, source_code)
  print("\nConditions between stop block and target block:\n",conditions)

  ##3. find the stop condition
  stop_condition, stop_con_line = findStopCondition(conditions_ids, ex_condition)

  #if all of the conditions are executed, select the last one
  if conditions and stop_condition == -1 and (conditions_ids[0] in ex_condition):
      stop_condition = conditions_ids[-1]

  #if none of the conditions are executed, find the nearest conditions before the stop block, and make one of them unsat
  if (not conditions) or (stop_condition == -1 and (conditions_ids[0] not in ex_condition)):
      print("\nnone of the conditions between stop and target were executed, selecting the last condition before stop block...")
      
      stop_condition, conditions = findLastCondition(stop_lineno, source_code)
      if stop_condition == -1:
        print("no conditions before stop block")
        restoreTargetFile(original_code, file_path)
        return -1, file_path, stop_block, db
      print("Stop block dominated by this condition", stop_condition, conditions[stop_condition])
      print("We need to make this condition unsat: ", stop_condition, conditions[stop_condition])
  else:
      print("Stop block dominated by this condition", stop_condition, conditions[stop_condition])
      print("We need to make this condition unsat: ", stop_condition, conditions[stop_condition])

  #from the stop_condition line, find all dependencies.
  stop_con_line = conditions[stop_condition][1]-offsetA
  print("Line number of the stop condition:",stop_con_line)

  #based on the condition, we search the data dependencies to see if there is any global variables we can fuzz.
  #query = "match (n {lineno:55, fileid:384827})<-[:REACHES]-(a) with a match (a)-[:PARENT_OF*]->(b) where b.code=\"_GET\" or b.code=\"_POST\" or b.code=\"error\" return b"
  toBeFuzzed = findToBeFuzzed(stop_con_line, fileid, conditions, stop_condition, graph)
  #print("The next parameter we can fuzz: ",toBeFuzzed)

  #if such condition is not found, we need to ask human to decide reach an intermediate point first
  conditions_to_store = []
  if not toBeFuzzed:
      print("No input seeds were found that control this condition")
      #print("No fuzz-able condition has been found, we need to unreach an intermediate point first:")
      toBeFuzzed, file_path, target_blockID, db = findSolveDPs(stop_con_line, fileid, conditions, stop_condition, offsetA, source_code, file_path, ex_block, target_blockID, graph)
      restoreTargetFile(original_code, file_path)
      restoreCondition(conditions, stop_condition, conditions_to_store)
      return toBeFuzzed, file_path, target_blockID, db
  else:
      restoreTargetFile(original_code, file_path)
      restoreCondition(conditions, stop_condition, conditions_to_store)
      return toBeFuzzed, file_path, target_blockID, db

  #print("TODO: if the chose block has already been reached, we should fuzz to un-reach that block")

###EXAMPLE OF PAGE password_reset.php
##set the target ID
#target_nodeID = 385315

##example of not given any parameters
##need unconver: set parameter account and key
#ex_block = [416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,1652819379617811,1652819379617814,1652819379617844,1652819379617847,1080768390496283,1080768390496285,1080768390496291,1080768390496295]
#ex_condition = [699,700,2222,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,19,21,28,2239,2238,2240,2243]

##example of given a random account and key: account=12345&key=12345
##need uncover: account is not email
#ex_block = [416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264149,1113762329264152,1113762329264153,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,1652819379617814,1652819379617817,1652819379617821,1652819379617843,1652819379617844,1652819379617847,1080768390496283,1080768390496285,1080768390496291,1080768390496295]
#ex_condition = [699,700,2222,2223,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,20,19,21,22,28,2239,2238,2240,2243]

##example of given a reasonable input: account=yshen55@uic.edu&key=12345
##need uncover: length of key is not 40
#ex_block = [416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264149,1113762329264152,1113762329264153,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,1652819379617814,1652819379617817,1117103813820462,1117103813820467,1117103813820468,1117103813820476,1652819379617825,1652819379617843,1652819379617844,1652819379617847,1080768390496283,1080768390496285,1080768390496291,1080768390496295]
#ex_condition = [699,700,2222,2223,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,20,19,21,2192,2194,2193,23,22,28,2239,2238,2240,2243]

##example of given a reasonable input: account=yshen55@uic.edu&key=1234512345123451234512345123451234512345
##need uncover: user info not in db? solved by create the account
#ex_block=[416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264149,1113762329264152,1113762329264153,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,1652819379617814,1652819379617817,1117103813820462,1117103813820467,1117103813820468,1117103813820476,1652819379617829,1652819379617839,1652819379617842,1652819379617843,1652819379617844,1652819379617847,1080768390496283,1080768390496285,1080768390496291,1080768390496295]
#ex_condition = [699,700,2222,2223,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,20,19,21,2192,2194,2193,23,22,24,28,2239,2238,2240,2243]

##example of given a reasonable input after create the account: account=yshen55@uic.edu&key=1234512345123451234512345123451234512345
##need uncover: password reset key not found
#ex_block=[416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264149,1113762329264152,1113762329264153,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,1652819379617814,1652819379617817,1117103813820462,1117103813820467,1117103813820468,1117103813820476,1652819379617829,1652819379617831,1652819379617834,1652819379617837,1652819379617842,1652819379617843,1652819379617844,1652819379617847,1080768390496283,1080768390496285,1080768390496291,1080768390496295]
#ex_condition = [699,700,2222,2223,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,20,19,21,2192,2194,2193,23,22,24,25,28,2239,2238,2240,2243]

##example of given a right input: {"account":"yshen55@uic.edu","key":"RJ6z8gYMAQ7XcjhjmUIWMtjDwi9sBoGvBlWGbId4"}
##successfully reached the target block
#ex_block = [416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264149,1113762329264152,1113762329264153,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,1652819379617814,1652819379617817,1117103813820462,1117103813820467,1117103813820468,1117103813820476,1652819379617829,1652819379617831,1652819379617837,1652819379617842,1652819379617843,1652819379617844,1652819379617848,1652819379617873,1107775144853615,1107775144853617,1107775144853618,1069433971802148,1080768390496333,1080768390496337,1080768390497283,1080768390497286,1110313470525547,1080768390496340,1080768390496544,1080768390496548,1080768390496549,1080768390496554,1080768390496555,1080768390496558,1080768390496560,1080768390496562,1080768390496568,1080768390496569,1080768390496601,1080768390496604,1080768390496521,1080768390496522,1080768390496533,1080768390496534,1080768390496535,1080768390496321,1080768390496310,1069433971802188,1069433971802192,1069433971802199,1069433971802200,1069433971802217,1069433971802220,1069433971802221,1069433971802226,1069433971802227,1069433971802229,1080768390497284,1069433971802483,245727963906066,245727963906070,236098647228557,236098647228561,635625095036932,635625095036935,635625095036943,635625095036945,635625095036948,1069433971802203,1069433971802216,1069433971802243,1069433971802253,1069433971802261,1069433971802269,1069433971802273,1069433971802275,1069433971802277,1069433971802364,1069433971802367,1069433971802342,1069433971802345,1069433971802352,405483567448091,405483567448100,1652819379617886,1069433971802252,1069433971802419,1069433971802423,1069433971802426,1069433971802427,1069433971802431,1069433971802435,1069433971802439,1069433971802450,1069433971802452,1069433971802456,1069433971802465,1069433971802466,1069433971802473,1069433971802474,1068768251871260,1068768251871270,1117589145125001,1117589145124897,1117589145124902,1117589145124903,1117589145124882,416487273660440]
#ex_condition = [699,700,2222,2223,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,20,19,21,2192,2194,2193,23,22,24,26,27,25,28,29,2211,2246,2385,2386,2272,2271,2273,2274,2275,2278,2268,2267,2269,2102,2101,2105,2107,2110,2109,2108,2117,2116,2119,2118,2120,2121,781,782,783,6720,6721,6722,2111,2122,2123,2128,2126,2125,2133,2134,2135,2165,2164,2156,2163,693,695,35,2124,2177,2178,2179,2181,2180,2182,2183,2186,2189,2188,2190,690,689,692,691,2065,697]


###EXAMPLE OF PAGE account_history_info.php
##set the target ID
#target_nodeID = 29149

##example of not given any parameters
##need unconver: user need to login
#ex_block = [416981194899478,416981194899479,416981194899486,1113762329264146,1113762329264154,416981194899502,416981194899505,1110313470525453,1110313470525457,1110313470525462,1110313470525463,236098647228454,236098647228502,236098647228534,236098647228469,1110313470525569,1110313470525485,1110313470525489,1110313470525539,236098647228459,236098647228465,416981194899526,416981194899538,416981194899563,1117589145124877,1117589145124921,1117589145124993,1117589145124994,1117589145125016,1117589145125017,416981194899587,1117589145124996,416981194899591,416981194899592,416981194899604,1080768390497193,1080768390497200,1080768390497201,416981194899608,416981194899612,1080768390497203,416981194899617,416981194899618,416981194899619,416981194899622,1117589145124924,1117589145124932,1117589145124940,1117589145124951,1117589145124955,1117589145124878,1117589145124886,1117589145124891,416981194899624,416981194899628,416981194899631,416981194899632,1117589145124977,416981194899636,1080768390497282,1080768390497289,1117589145124963,1117589145124966,1117589145124968,1117589145124971,416981194899638,416981194899655,416981194899669,416981194899683,416981194899687,1117589145124967,1107775144853601,1107775144853605,1107775144853571,1107775144853548,1107775144853552,1107775144853553,1107775144853554,1107775144853557,1107775144853558,1107775144853559,1107775144853562,1107775144853564,1107775144853563,1107775144853540,1107775144853536,1107775144853565,1107775144853566,1107775144853567,1107775144853517,1107775144853520,1107775144853521,1107775144853522,1107775144853530,1107775144853526,1107775144853531,1107775144853532,1107775144853582,1107775144853593,1107775144853595,1107775144853607,1107775144853613,1107775144853619,1107775144853622,416981194899689,416981194899696,416981194899697,416981194899699,416981194899706,416981194899707,416981194899711,1069433971802127,1080768390496309,1080768390496312,1080768390496313,1080768390496305,1069433971802133,1069433971802138,1069433971802141,1069433971802142,1069433971802145,1069433971802151,1069433971802153,1069433971802159,1069433971802160,1069433971802165,1069433971802166,1069433971802169,1069433971802170,1069433971802179,1069433971802180,416981194899720,416981194899725,416981194899726,416981194899727,416981194899731,416981194899733,416981194899760,1115742309187597,1115742309187607,1115742309187609,1117589145124985,1117589145124988,1080768390497302,1080768390497315,1080768390497319,1080768390497323,1080768390497327,1080768390497332,1080768390497298,1080768390497333,1080768390497336,1110313470525575,1110313470525576,1080768390496325,1110313470525543,1115742309187626,1115742309187627,1080411908210709,1080411908210714,416981194899784,416981194899785,416981194899794,416981194899795,1069433971802136,416981194899828,416981194899842,236098647228540,236098647228508,236098647228509,236098647228510,236098647228511,236098647228512,236098647228516,236098647228519,236098647228521,236098647228526,236098647228527,236098647228436,236098647228438,236098647228428,236098647228429,236098647228430,236098647228439,236098647228530,236098647228531,236098647228532,236098647228533,236098647228460,236098647228461,236098647228462,236098647228463,236098647228464,236098647228551,236098647228552,236098647228553,236098647228558,236098647228562,124296353546255,1080768390496283,1080768390496285,1080768390496291,1080768390496295]
#ex_condition = [699,700,2222,702,704,2212,2213,2529,2216,706,711,2063,2079,2081,717,718,719,724,2372,2375,2376,2374,726,727,729,2066,2069,2072,2074,2217,2064,730,2077,731,2384,2075,2076,733,739,742,745,2207,2201,2202,2203,2204,2205,2197,2198,2199,2200,2206,2208,2209,747,749,750,2244,2245,2083,2084,2085,2086,2087,2089,2090,2088,2092,2091,2098,2099,752,756,757,760,761,2210,763,2225,2078,2388,2391,2393,2395,2398,2397,2220,2226,2221,767,769,770,777,2528,2530,2531,2532,2533,2521,2522,2534,2536,199,2239,2238,2240,2243]

#Get CFG path from satpath.json
def getPath(file):
  f=open(file,"r")
  paths = json.loads(f.read())
  f.close()
  return paths

#Get all the target nodes we want to reach
def getTargets(paths):
  targets = []
  for path in paths:
    if isinstance(path[0], list):
      path=path[0]
    if path[-1] not in targets:
      targets.append(path[-1])
  return targets

#Get the nodes that we already processed
def getProcessedNodes():
  f=open("processed","r")
  processed = json.loads(f.read())
  f.close()
  return processed

#Update the nodes that we already processed
def updateProcessedNodes(processed):
  f=open("processed","w")
  f.write(json.dumps(processed))
  f.close()

#Generate input based on the model files generated by static analysis
def Gen_in(target_nodeID):
    filepath = "/home/user/Downloads/uic-master/navex_docker/chess-navex/report/"
    raw = os.listdir(filepath)
    #index = 0
    for file in raw:
        if file[-6:] == '.model' and str(target_nodeID) in file:
            #start = file.find(target_nodeID)+len(str(target_nodeID))+1
            #index = int(file[start: file.find("_", start)])
            #if index:
            result = Gen_input(filepath+file)
            if result != -1:
                print("Extracting seeds and values from static analysis results: ", filepath+file)
                print("Seeds and values: ", result)
                return result
    return -1

#modify the input file of AFL fuzzer
def writeInputs(inputs):
  file = "./input/test1.txt"
  f = open(file, "w")
  f.write(json.dumps(inputs))
  f.close()

#Modify the input array(That happends before write the inputs to AFL input file and before the fuzzer process starts)
def changeInput(inputs):
    paramName = input("Please enter the param name you want to modify/add:")
    paramValue = input("Please enter the param value:")
    paramType = input("Please enter the type of the param:")
    if paramName in inputs:
        inputs[paramName][0] = paramValue
        inputs[paramName][1] = paramType
    else:
        inputs[paramName] = [paramValue, paramType]
    return inputs

#Try to solve the sub-question by modifying the inputs
def solveSubQ(condition, inputs):

    print("The current input: ", inputs)
    dec = input("Can you do anything to make the target condition unsat? (Y to continue, N to quit this case, I to change input)")
    if dec == "Y":
        return inputs
    elif dec == "I":
        inputs = changeInput(inputs)
        return inputs
    else:
        return -1

#Delete the duplicated items in array a
def deleteDup(a):
    temp = []
    for  i in a:
        if i not in temp:
            temp.append(i)
    return temp

#This function is used when AFL is necessary to be used to get the right input. It generates a command to call AFL to solve specific problems
#For example, which file to fuzz(url), what is the target block(targetBlock), HTTP method to use(GET), The name of the parameter that we need to fuzz(paramName)
#, wether we should reach or unreach the target(action) and the mutation type.
def DoFuzz(toBeFuzzed, file_path, inputs, targetBlock, action):
    mut = "String"
    toBeFuzzed = deleteDup(toBeFuzzed)
    original_code = instrumentTargetFile(file_path)
    paramName, paramType = getParamName(toBeFuzzed[0])
    print("The next parameter we can fuzz: ", toBeFuzzed, " name:", paramName, " type:", paramType)
    if inputs == -1:
        inputs = {}
    dec = input("Do you want to continue to fuzz process?(N to skip)")
    if dec == "N":
        return 0
    dec = input("Do regex mutation?(Y/N)")
    patten = ""
    example = ""
    if dec == "Y":
        mut = "regex"
        patten = input("Please enter the patten for parameter "+str(paramName)+":\n")
    else:
        if paramName not in inputs:
            seed = input("Please provide an example of the parameter value:")
            inputs[paramName]=[seed, paramType]
        else:
            dec = input("Do you want to privide an example for parameter "+str(paramName)+"?(Y/N)")
            if dec == "Y":
                seed = input("Please provide an example of the parameter value:")
                inputs[paramName]=[seed, paramType]
        mut = paramType
    writeInputs(inputs)
    print(json.dumps(inputs))
    url = "http://"+file_path.replace("/var/www/html","localhost")
    #cmd = "sudo ./afl-fuzz -i input -o output -m 500 "+url+" "+str(targetBlock)+" GET key "+str(action)+" regex"+str(mut)
    if mut == "regex":
        cmd = "sudo ./afl-fuzz -i input -o output -m 500 "+url+" "+str(targetBlock)+" GET "+str(paramName)+" "+str(action)+" regex"+str(patten)
    else:
        cmd = "sudo ./afl-fuzz -i input -o output -m 500 "+url+" "+str(targetBlock)+" GET "+str(paramName)+" "+str(action)+" None"
    #cmd = "sudo ./afl-fuzz -i input -o output -m 500 "+url+" "+str(targetBlock)+" GET "+str(paramName)+" "+str(action)+" regex"+str(mut)
    print(cmd)
    return_state = os.system(cmd)
    restoreTargetFile(original_code, file_path)
    return return_state,paramName

#Get the input value of last record in trace infomation table
def getParamValueInDB(id, db):
  result = []
  query = "SELECT input FROM cephoenix WHERE id="+str(id)

  cursor = db.cursor()
  cursor.execute(query)
  result = list(cursor.fetchall())
  cursor.close()

  if not result:
    time.sleep(1.0)
    db = dbRefresh(db)
    cursor = db.cursor()
    cursor.execute(query)
    result = list(cursor.fetchall())
    cursor.close()
    if not result:
      return -1,db

  return json.loads(result[0][0]), db


#Get the input value of last record in trace infomation table
def getInputInDB(paramName, inputs, db):
    id,db = getTotalRecords(db)
    i,db = getParamValueInDB(id, db)
    if paramName in i:
        inputs[paramName][0] = i[paramName]
    else:
        return -1, db
    return inputs, db


#Start of the script, here is actually the main function
offsetA=42
#inputs={385315:{"account": "\\x0", "confirmation": "", "password": "", "key": "", "action": "proces", "formid": "\\x00\\x0"}}
filepath = "/home/user/Downloads/uic-master/navex_docker/chess-navex/report/sat_path/"
processed = getProcessedNodes()
paths = getPath(filepath+"satpaths_all.json")
targets = getTargets(paths)
#targets=[272591]

for target_nodeID in targets:
  if target_nodeID not in processed:
    lineno, fileid = getNodeLineno(target_nodeID, graph)
    toBeFuzzed = []
    file_path = ""
    targetBlock = 0
    action = "r"
    mut = "string"

    #print("Extrating seeds and values from static analysis:")
    inputs = Gen_in(target_nodeID)
    if inputs!=-1:
        toBeFuzzed, file_path, targetBlock, db = nextToFuzz(target_nodeID, db, graph, inputs)
    else:
        toBeFuzzed, file_path, targetBlock, db = nextToFuzz(target_nodeID, db, graph)

    while toBeFuzzed == "subQ":
        dec = input("Press Enter to solve the Sub-question. N to exit from this case: ")
        if dec == "N":
            break

        toBeFuzzed = []
        for i in targetBlock:
            if i!="blockID":
                temp = findToBeFuzzed(targetBlock[i][1]-offsetA, fileid, targetBlock, i, graph)
                for t in temp:
                    if t not in toBeFuzzed:
                        toBeFuzzed.append(t)
        if toBeFuzzed:
            print("we find some params to fuzz:")
            for i in range(len(toBeFuzzed)):
                paramName, paramType = getParamName(toBeFuzzed[i])
                print("ID:", toBeFuzzed[i], "name:", paramName, " type:", paramType)
            dec = input("should we start fuzzing from the first param(Y)? or you want to solve it manually(N)?")
            if dec == "Y":
                action = input("Should reach(r) or unreach(u) the target?")
                #action = "u"
                targetBlock = targetBlock["blockID"]
                state, paramName = DoFuzz(toBeFuzzed, file_path, inputs, targetBlock, action)
                inputs, db = getInputInDB(paramName, inputs, db)
                print("The inputs we used to pass last sub-question: ", inputs)
                #break
            else:
                if inputs == -1:
                    inputs = solveSubQ(targetBlock, {})
                else:
                    inputs = solveSubQ(targetBlock, inputs)
                if inputs == -1:
                    break
        else:
            print("Did not find any param that we can fuzz. You need to solve it manually")

            if inputs == -1:
                inputs = solveSubQ(targetBlock, {})
            else:
                inputs = solveSubQ(targetBlock, inputs)
        if inputs == -1:
            break
        db = dbRefresh(db)
        toBeFuzzed, file_path, targetBlock, db = nextToFuzz(target_nodeID, db, graph, inputs)


    if toBeFuzzed != -1 and toBeFuzzed != "subQ" and inputs!=-1:
        DoFuzz(toBeFuzzed, file_path, inputs, targetBlock, action)
    input("Press enter to continue fuzz next target:")
    processed.append(target_nodeID)
    updateProcessedNodes(processed)
try:
    db.close()
except:
    pass
