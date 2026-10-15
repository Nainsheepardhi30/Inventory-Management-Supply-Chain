import numpy as np
import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Ayush2005",
    database="python_ui_project"
)


def connect_to_database():
    return conn


# create agent 

db = connect_to_database()
cursor = db.cursor(dictionary=True)

# test agent it is working or not
cursor.execute("SELECT COUNT(*) FROM suppliers")
result = cursor.fetchone()
# print(list(result.values())[0])


def get_basic_info():
    queries = {
                "Total Suppliers" : "SELECT COUNT(*) FROM suppliers;" ,
                
                "Total Products" : "SELECT COUNT(*) FROM products;" ,
                
                "Total Categories Dealing" : "SELECT COUNT(DISTINCT category) FROM products;" ,
                
                "Total sale value in last 3 months " : """  
                SELECT SUM(ABS(se.change_quantity) * p.price)
                FROM stock_entries AS se
                JOIN products p 
                ON p.product_id = se.product_id
                WHERE se.change_type = 'sale'
                AND 
                se.entry_date >=
                (
                SELECT DATE_SUB(MAX(entry_date),INTERVAL 3 MONTH) FROM stock_entries
                );
                """ ,
                
                "Total restock value in last 3 months " : """  
                SELECT SUM(ABS(se.change_quantity) * p.price)
                FROM stock_entries AS se
                JOIN products p 
                ON p.product_id = se.product_id
                WHERE se.change_type = 'restock'
                AND 
                se.entry_date >=
                (
                SELECT DATE_SUB(MAX(entry_date),INTERVAL 3 MONTH) FROM stock_entries
                );
                """,
                
                "Bellow Reorder & No Pending Reorders" : """  
                SELECT COUNT(*) FROM products as p WHERE p.stock_quantity < p.reorder_level
                AND product_id NOT IN 
                (
                SELECT DISTINCT product_id FROM reorders WHERE status = 'pending'
                )
                """
            }

    result = {}
    for key , query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()
        result[key] = list(row.values())[0]
    
    return result




def get_additional_table():
    queries = {

                "Suppliers and There Contact Details" : "SELECT supplier_name, contact_name, email, phone FROM suppliers",

                "Product With There Suppliers and Current Stock" : """
                SELECT product_name, supplier_name, stock_quantity, reorder_level 
                FROM products as p
                JOIN suppliers s
                ON p.supplier_id = s.supplier_id
                ORDER BY product_name;
                """,

                " Product Needing Reorder" : "SELECT product_id, product_name, stock_quantity, reorder_level FROM products WHERE stock_quantity < reorder_level ;"

            }

    table = {}
    for lable , data in queries.items():
        cursor.execute(data)
        table[lable] = cursor.fetchall()
    
    return table


def add_new_manual_id(cursor, db, p_name,p_category,p_price,p_stock,p_reorder,p_supplier):
    proc_call = "CALL add_newproduct_manualID(%s, %s, %s, %s, %s, %s)"
    params = (p_name, p_category, p_price, p_stock, p_reorder, p_supplier)
    cursor.execute(proc_call, params)
    db.commit()

def get_categories(cursor):
    cursor.execute("SELECT DISTINCT category FROM products order by category asc;")
    rows = cursor.fetchall()
    categories = [row['category'] for row in rows]
    return categories

def get_suppliers(cursor):
    cursor.execute("SELECT supplier_id, supplier_name FROM suppliers order by supplier_name asc;")
    suppliers = cursor.fetchall() 
    return suppliers


def get_all_products (cursor):
    cursor.execute("SELECT product_id, product_name FROM products ORDER BY product_name ;")
    return cursor.fetchall()

def get_product_history(cursor, product_id):
    quEry = "SELECT * FROM product_history WHERE product_id = %s ORDER BY record_date DESC;"
    cursor.execute(quEry, (product_id,))
    return cursor.fetchall()

def place_reorder(cursor, db, product_id, reorder_quantity):
    query = '''
        INSERT INTO reorders(reorder_id, product_id, reorder_quantity, reorder_date, status)
        SELECT 
        MAX(reorder_id)+1,
        %s,
        %s,
        CURDATE(), 
        "ordered" FROM reorders  
        '''
    cursor.execute(query, (product_id, reorder_quantity))
    db.commit() 

    

def get_pending_reorders(cursor):
    query = '''
        SELECT reorder_id , product_name
        FROM reorders AS r
        JOIN products AS p 
        ON r.product_id = p.product_id
        WHERE r.status != 'received';
    '''
    cursor.execute(query)
    return cursor.fetchall()

def mark_reorder_as_received(cursor, db, reorder_id):
    cursor.callproc('MarkReorderAsReceived', [reorder_id])
    db.commit()