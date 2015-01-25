import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1',
                               user='root', 
                               # Don't forget to change the next two lines, as needed.
                               password='itcarlow', 
                               database='buzzers', )

cursor = conn.cursor()

flights={}
# Create the SQL needed, then execute() it - be sure to test the SQL at the mysql> prompt first.
SQL = """select * from flights"""  
cursor.execute( SQL )
# To get all the results in one go, use fetchall()
for row in cursor.fetchall():
    data=[row[0], row[1]]  # Each item in the row tuple corresponds to a column in your table.
    numbers = data[0::1]
    words = data[1::2]
    flights.update(dict(zip(numbers, words)))

conn.commit()
conn.close()