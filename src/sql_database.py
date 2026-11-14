from pyspark.sql import DataFrame, SparkSession
from configs.configs import DatabaseConfig

import json
from contextlib import closing
from datetime import date
import mysql.connector


TRANSACTION_COLUMNS = ("chck_date", "payment_type", "category", "amount", "fraud")

TRANSACTION_SCHEMA = """
    chck_date TIMESTAMP,
    payment_type STRING,
    category STRING,
    amount DOUBLE,
    fraud BOOLEAN
"""

FEATURE_COLUMNS = ( "amount", "fraud", "z_score", "z_score_by_category", 
                   "enc_category", "enc_payment_type", "is_large_transaction")

FEATURE_SCHEMA = """
    amount DOUBLE,
    fraud BOOLEAN,
    z_score DOUBLE,
    z_score_by_category DOUBLE,
    enc_category ARRAY<DOUBLE>,
    enc_payment_type ARRAY<DOUBLE>,
    is_large_transaction BOOLEAN
"""

TABLES = {
    "raw_transactions": ( TRANSACTION_COLUMNS, TRANSACTION_SCHEMA), 
    "preprocessed_transactions":(TRANSACTION_COLUMNS, TRANSACTION_SCHEMA), 
    "transaction_features": ( FEATURE_COLUMNS, FEATURE_SCHEMA), 
}

ARRAY_COLUMNS = ("enc_category", "enc_payment_type")
BOOLEAN_COLUMNS = ("fraud", "is_large_transaction")


def get_connection():
    return mysql.connector.connect(
        host=DatabaseConfig.host,
        port=DatabaseConfig.port,
        database=DatabaseConfig.database,
        user=DatabaseConfig.user,
        password=DatabaseConfig.password,
        autocommit=False)
    
    
def read_data(table: str, start_date: date | None = None) -> DataFrame:  
    columns, schema = TABLES[table]

    query = f"SELECT {', '.join(columns)} FROM {table}" 
    parameters = () 

    if start_date is not None: 
        query += " WHERE chck_date >= %s"  
        parameters = (start_date,) 

    with closing(get_connection()) as connection:
        with closing(connection.cursor(dictionary=True)) as cursor:
            cursor.execute(query, parameters)  
            rows = cursor.fetchall() 

    for row in rows: 
        for column in ARRAY_COLUMNS: # handeling encodings and categories 
            if column in row and row[column] is not None:
                row[column] = json.loads(row[column])

        for column in BOOLEAN_COLUMNS: # handeling boolean features and the label
            if column in row and row[column] is not None:
                row[column] = bool(row[column]) 
 
    spark = SparkSession.builder.master("local[2]").getOrCreate()

    return spark.createDataFrame(rows, schema=schema)


def write_data( data: DataFrame, table: str, batch_size: int = 10000) -> None:
    # this function replaces the parqet overwrite behavior
    # it deletes prev rows, inserts new ones and commits
    columns, bla = TABLES[table]

    placeholders = ", ".join(["%s"]* len(columns)) 

    sql_insert_query = ( f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})")

    with closing(get_connection()) as connection:
        with closing(connection.cursor()) as cursor:
            try:
                cursor.execute(f"DELETE FROM {table}")
                batch=[] 

                for row in data.select(*columns).toLocalIterator():
                    record = row.asDict()
                    values=[] 

                    for column in columns:
                        value = record[column]

                        if column in ARRAY_COLUMNS and value is not None:
                            value = json.dumps(value) # we store arrays as json

                        values.append(value) 

                    batch.append(tuple(values))

                    if len(batch) == batch_size:
                        cursor.executemany(sql_insert_query, batch) # multiple rows at a time 
                        batch.clear()

                if batch:
                    cursor.executemany(sql_insert_query, batch)

                connection.commit()

            except Exception: # if something fails then we rollback to prev commit table
                connection.rollback()
                raise