from py2neo import Graph
import json

def getFileIDs(graph):
    #query = "MATCH (a {id:"+str(nodeID)+"}) return a" #dokan and oscommerce
    query = "MATCH (n:Filesystem) return n.full_name, n.fileid" # all oth$
    result = graph.run(query).data()
    fileID = {}
    for y in result:
        fileID[y["n.full_name"]] = y["n.fileid"]
    return fileID

#graph = Graph(auth=('neo4j', 'neo'))
def Gen_input(file):
    g_v = ["_GET", "_POST"]

    f = open(file, "r")
    lines = f.readlines()
    f.close()
    if lines[0][:5] == "unsat" or lines[0][:7] == "timeout":
        return -1
    result = []
    for i in range(len(lines)):
        if "define-fun" in lines[i]:
            temp = lines[i][lines[i].find("define-fun")+11:-1].split(" ")
            temp_r = [temp[0], temp[2]]
            temp_r.append(lines[i+1][:-2].strip().replace("\\\\","\\"))
            if temp_r[-2] == 'String':
              temp_r[-1] = temp_r[-1][1:-1]
            #print(temp_r)
            result.append(temp_r)

    parameter = {}
    for r in result:
        for p in g_v:
            if p in r[0]:
                start_idx = r[0].find(p)+len(p)+1
                end_idx = len(r[0])-1
                while r[0][end_idx]!='_':
                    end_idx-=1
                temp = r[0][start_idx:end_idx]
                parameter[temp]=[r[2], r[1], p]
                #parameter[temp] = r[2]
    #print(parameter)
    return parameter

#print(Gen_input("test.model"))

