import mariadb

db = mariadb.connect(
    user = "jyw",
    password = "yewon",
    host = "localhost",
    port = 3306,
    database = "IOT"
)
cur = db.cursor(dictionary = True)

cur.execute("select * from Controller")
while True:
    status = cur.fetchone()
    if not status: break
    print(status)

cur.close()
db.close()