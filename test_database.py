from mysql import connector

username = 'root'
password = 'root'
host = 'localhost'

conn = connector.connect(
        host=host,
        user=username,
        password=password,
        database='bets'
    )

# cursor = conn.cursor(buffered=True, dictionary=True)
cursor = conn.cursor()

sql = """select idmatch
 from `match`;"""
cursor.execute(sql)
print(cursor.fetchone())
conn.close()

