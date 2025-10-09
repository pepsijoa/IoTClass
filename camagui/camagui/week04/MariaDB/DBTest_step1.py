import mariadb

db = mariadb.connect(
    user="camagui",
    password="power2",
    host="localhost",
    port=3306,
    database="IOT")
cur = db.cursor()

cur.execute("select * from Controller")
while True:
    status = cur.fetchone()
    if not status: break
    print(status)
    
cur.close
db.close()
