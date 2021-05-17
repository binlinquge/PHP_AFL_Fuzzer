import sys
import os
from py2neo import Graph

def getFileIDs(graph):
    #query = "MATCH (a {id:"+str(nodeID)+"}) return a" #dokan and oscommerce
    query = "MATCH (n:Filesystem) return n.full_name, n.fileid" # all oth$
    result = graph.run(query).data()
    fileID = {}
    for y in result:
        fileID[y["n.full_name"]] = y["n.fileid"]
    return fileID

def Reinstrement(file, fileid, total_block, total_conditions):
    try:
        f = open(file, "r")
        content = f.readlines()
        f.close()
    except:
        print("Error open file ", file)
        return 0,0

    f2 = open("condition.log", "a")
    block_nums = 0
    for lineno in range(len(content)):
        if "BLOCK_INDEX_PLACE_HOLDER" in content[lineno]:
            block_index = (fileid << 32) + lineno
            content[lineno] = content[lineno].replace("BLOCK_INDEX_PLACE_HOLDER", str(block_index))
            block_nums+=1
        if "BLOCK_CONDITION_INDEX_PLACE_HOLDER" in content[lineno]:
            f2.write(content[lineno])
        while "BLOCK_CONDITION_INDEX_PLACE_HOLDER" in content[lineno]:
            content[lineno] = content[lineno].replace("BLOCK_CONDITION_INDEX_PLACE_HOLDER", str(total_conditions), 1)
            total_conditions += 1
    f2.close()

    total_block += block_nums
    header = """final class FuzzingContext {
        public static $prevBlock = 0;
        public static $edges = [];

        public static function reset() {
            self::$prevBlock = 0;
            self::$edges = [];
        }

        public static function traceBlock($blockIndex, $returnValue) {
            $key = $blockIndex;
            self::$edges[$key] = (self::$edges[$key] ?? 0) + 1;
            return $returnValue;
        }
    }
    """

    f = open(file, "w")
    #f.write(content[0])
    #f.write(header)
    for line in content:
        f.write(line)
    f.close()
    return total_block, total_conditions

root = sys.argv[1]
#os.mkdir(root+"_ins")
filepath = [sys.argv[1]]

graph = Graph(auth=('neo4j', 'neo'))
fileID = getFileIDs(graph)
#print(fileID)

total_block = 0
total_condition = 0

while filepath:
    path = filepath.pop(0)
    path = path+"/"
    print("current path: " + path)

    raw = os.listdir(path)
    files = []
    for x in raw:
        if os.path.isdir(path + x):
            filepath.append(path + x)
        else:
            if x[-4:] == ".php":
                files.append(path + x)

    path = path.replace(root, root+"_ins")
    print("instremented path: " + path)
    os.mkdir(path)

    if "./collabtive/vendor/ensepar/tcpdf/tcpdf.php" in files:
        idx=files.index("./collabtive/vendor/ensepar/tcpdf/tcpdf.php")
        files.pop(idx)

    for file in files:
        file2 = file.replace(root, root+"_ins")
        if not os.system("php instrument.php "+ file.replace("(", "\(").replace(")", "\)") + " "+file2.replace("(", "\(").replace(")", "\)")):
            print("php instrument.php "+file + " "+file2)


    for file in files:
        S_path = file.replace(".", "/var/www/html",1)
        if S_path not in fileID:
            print("File "+S_path+" is not in the neo4j DB.")
            continue
        print(S_path)
        fileid = fileID[S_path]
        if not fileid:
            continue
        total_block,total_condition = Reinstrement(file.replace(root, root+"_ins"), fileid, total_block, total_condition)
        #break

print("Total block: ", total_block)
print("Total conditions: ",total_condition)
