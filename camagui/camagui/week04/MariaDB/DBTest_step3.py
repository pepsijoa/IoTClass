import mariadb

db = mariadb.connect(
    user="camagui",
    password="power2",
    host="localhost",
    port=3306,
    database="IOT"
)

cur=db.cursor()

#Drop the table if it exists
SQL = '''
    DROP TABLE IF EXISTS Controller2
'''

cur.execute(SQL)
#Create a new table
SQL = '''
    CREATE TABLE Controller2 (
    id int auto_increment not null primary key,
    aircon char(10),
    heater char(10),
    dryer char(10),
    temp char(10),
    humid char(10),
    dt datetime default current_timestamp
    )
'''
cur.execute(SQL)

#Insert some data
cur.execute("insert into Controller2 (aircon, heater, dryer) values ('ON', 'OFF', 'OFF')")
cur.execute("insert into Controller2 (aircon, heater, dryer) values ('OFF', 'ON', 'OFF')")
cur.execute("insert into Controller2 (aircon, heater, dryer) values ('OFF', 'OFF', 'ON')")
db.commit()

cur.execute("select * from Controller2")
while True:
    status = cur.fetchone()
    if not status: break
    print(status)

cur.close()
db.close()