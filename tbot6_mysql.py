import mysql
import pandas as pd
from mysql.connector import Error

sqlhost = 'localhost'
sqluser = 'pycrypto'
sqlpass = 'Viloria21!'
sqldb   = 'dbcrypto'


create_crp_table = """
CREATE TABLE crp (
  crp_id      CHAR PRIMARY KEY,
  crp_purdate DATE,
  crp_purtime TIME,
  crp_qty       DECIMAL,
  crp_value1    DECIMAL,
  crp_value     DECIMAL
  );
 """


def create_server_connection(host_name, user_name, user_password):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            auth_plugin='mysql_native_password'
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection

def create_db_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name,
            auth_plugin='mysql_native_password'
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection

def create_database(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute('CREATE DATABASE '+query)
        print("Database created successfully")
    except Error as err:
        print(f"Error: '{err}'")

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")

def read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
        print(f"Error: '{err}'")





#connection = create_server_connection("localhost","icirauqui","Viloria21!")
#create_database(connection,"dbcrypto")
#connection = create_db_connection(sqlhost,sqluser,sqlpass,sqldb)
#execute_query(connection,create_crp_table)