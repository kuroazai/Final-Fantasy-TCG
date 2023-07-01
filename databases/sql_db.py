import mysql.connector
import glob


class SqlDatabase:

    def __init__(self):
        self.conn = mysql.connector.connect(
                                        user="root",
                                        password="",
                                        host="127.0.0.2",
                                        port=3306,
                                        database="fftcg"

                                      )
        self.cursor = self.conn.cursor()
        self.conn.autocommit = True

    def terminate(self):
        self.cursor.close()

    def append_table(self, values):
        stmt = 'SELECT code FROM cards WHERE code = "{}"'.format(values[10])
        self.cursor.execute(stmt)

        myresult = self.cursor.fetchall()

        if myresult:
            print(values[10], 'Already exists')
            return False

        mySql_insert_query = """INSERT INTO Cards (Name, Effect, Type, Element, Cost, Serial, Job, Power, Catagory, Boxset, Code, Image)
                               VALUES {}
                                """.format(values)

        self.cursor.execute(mySql_insert_query)
        self.conn.commit()
        print(self.cursor.rowcount, " {} Record inserted successfully into cards table".format(values[10]))
        return True

    def retrieve_query(self, column):
        stmt = 'SELECT {} FROM cards'.format(column)
        self.cursor.execute(stmt)
        myresult = self.cursor.fetchall()
        print(len(myresult))
        return myresult


def create_card_table():
    dbloc = r'C:\xampp\mysql\data\fftcg'
    if glob.glob(dbloc + '/cards.*'):
        print('Table exists')
    else:
        DB.cursor.execute("CREATE TABLE CARDS (Name VARCHAR(255), Effect VARCHAR(255), Type VARCHAR(255), Element VARCHAR(255), Cost VARCHAR(255), Serial VARCHAR(255), Job VARCHAR(255), Power VARCHAR(255), Catagory VARCHAR(255), Boxset VARCHAR(255), Code VARCHAR(255))")
        print('Generated New Table')


if __name__ == '__main__':
    DB = SqlDatabase()
    create_card_table()
    DB.terminate()
