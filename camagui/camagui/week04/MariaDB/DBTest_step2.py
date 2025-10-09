import mariadb

db = mariadb.connect(
    user="camagui",
    password="power2",
    host="localhost",
    port=3306,
    database="IOT")

cur=db.cursor(dictionary=True)

cur.execute("select * from Controller")

status = cur.fetchall()

print(status)

cur.close()
db.close()
