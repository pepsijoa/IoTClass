import mariadb

db = mariadb.connect(
    user="camagui",
    password="power2",
    host="localhost",
    port=3306,
    database="IOT"
)
cur=db.cursor()

state = {
    "aircon": "OFF",
    "heater": "OFF",
    "dryer": "ON",
    "temp": "26.5",
    "humid": "45.5"
}

#update Latest Data

SQL = "UPDATE Controller2 SET temp = %s, humid = %s where id = (select max(id) from Controller2)"
parameter = [state["temp"], state["humid"]]
cur.execute(SQL, parameter)
db.commit()

cur.execute("select * from Controller2")
while True:
    status = cur.fetchone()
    if not status: break
    print(status)

cur.close()
db.close()