import pymysql

def createTable():
  db = pymysql.connect(host="localhost",user="fuzz",passwd="User_123",db="fuzz")

  cursor = db.cursor()

  sql="""create table cephoenix (
     id int not null AUTO_INCREMENT,
     file_name char(50),
     ex_block text,
     ex_condition text,
     input text,
     PRIMARY KEY (id))
  """

  try:
    cursor.execute(sql)
    print("success to create table cephoenix")
  except Exception as e:
    print("fail to create database: %s"%e)
  finally:
    cursor.close()
    db.close()

createTable()
