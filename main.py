from typing import Annotated
from fastapi import FastAPI, HTTPException, File, UploadFile
from data_models import *
import pyodbc
from data_models import *
import bcrypt
import datetime
import os.path

save_path = 'D:\\BANCHANGTONG\\APIs\\bctAPIs\\images'

server = "DESKTOP-U71JKDK\\SQLEXPRESS"
database = "banchangtong"
username = ""
password = ""
app = FastAPI()

conn_str = f"Driver={{SQL Server}};Server={server};Database={database};UID={username}"


@app.post("/insertProduct")
async def insert_product(productCategory : str, createBy : int, imagePath : str, price : int, basePrice : str, material : list, diamond : list, gemstone : list, file: UploadFile):
    time = datetime.datetime.now()

    filename = (file.filename)
    with open('{0}\\{1}'.format(save_path,filename), 'wb+') as f:
        f.write(file.file.read())

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Fetch the latest ProductId based on ProductCategory
        cursor.execute(
            "SELECT TOP 1 ProductId FROM [Product] WHERE ProductCategory = ? ORDER BY Id DESC",
            (productCategory)
        )
        row = cursor.fetchone()
        print(row)

        if row:
            product_id = int(row[0]) + 1
            product_code = productCategory + str(product_id)
            print(product_code)
            #print(material)

            # Batch insert for Product, ProductDetail, and ProductMaterial

            # cursor.executemany(
            #     "INSERT INTO Product (ProductCode, ProductId, ProductCategory, CreateDate, CreateBy) VALUES (?, ?, ?, ?, ?, ?)",
            #     [(product_code, product_id, productCategory, time, createBy)]
            # )

            # cursor.executemany(
            #     "INSERT INTO ProductDetail (ProductId, ImagePath, Price, BasePrice) VALUES (?, ?, ?, ?)",
            #     [(product_id, imagePath, price, basePrice)]
            # )

            # cursor.executemany(
            #     "INSERT INTO ProductMaterial (ProductId, MaterialType, MaterialWeight, MaterialPercent) VALUES (?, ?, ?, ?)",
            #     [(product_id, mat['MaterialType'], mat['MaterialWeight'], mat['MaterialPercent']) for mat in material]
            # )

            # Batch insert for ProductDiamonds
            # if diamond == []:
            #     print("diamond ว่าง")
            # else:
            #     cursor.executemany(
            #     "INSERT INTO ProductDiamonds (ProductId, Carat, Color, Cut, Clarity, Certificated, Amount, CreateDate, CreateBy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            #     [(product_id, dia['Carat'], dia['Color'], dia['Cut'], dia['Clarity'], dia['Certificated'], dia['Amount'], time, createBy) for dia in diamond]
            # )

            # if gemstone == []:
            #     print("gemstone ว่าง")
            # else:
            #     cursor.executemany(
            #     "INSERT INTO ProductGems (ProductId, Carat, Shape, Color, Price, CreateDate, CreateBy) VALUES (?, ?, ?, ?, ?, ?, ?)",
            #     [(product_id, gems['Carat'], gems['Shape'], gems['Color'], gems['Price'], time, createBy) for gems in gemstone]
            # )

            # Commit the transaction after all insertions are done.
            conn.commit()

            return {"message": "Insert Success", "data": [{"productCategory": productCategory, "diamond": diamond, "gemstone": gemstone, "material": material}]}
        else:
            return {"message": "Insert fail"}

    except pyodbc.Error as e:
        print(f"Error during insert: {e}")
        return {"message": "An error occurred during insert"}

    finally:
        cursor.close()
        conn.close()

@app.post("/getProduct")
async def insert_product(data: GetProduct) -> dict:
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM Product WHERE ProductId = ?", (data.productId)
        )
            # Commit the transaction after all insertions are done.
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.commit()

        return {"message": "Get product detail Success", "data": results}

    except pyodbc.Error as e:
        print(f"Error during read: {e}")
        return {"message": "An error occurred during read"}

    finally:
        cursor.close()
        conn.close()


# -------------------- Register & Login ----------------------


@app.post("/register")
async def register(data: RegisterData) -> dict:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        # Check existing username
        if is_existing_username(cursor, data.username):
            raise HTTPException(status_code=409, detail="Username already exists")

        # Hash password
        hashed_password = hash_password(data.password)
        
        # Insert new user
        insert_user(cursor, data.username, hashed_password)
        
        conn.commit()
        return {"message": "User registered successfully"}
    except pyodbc.Error as e:
        print(f"Error inserting data: {e}")
        return {"message": "Failed to register user"}
    finally:
        cursor.close()
        conn.close()

def is_existing_username(cursor, username: str) -> bool:
    query = "SELECT COUNT(*) FROM [User] WHERE username = ?"
    cursor.execute(query, username)
    existing_user_count = cursor.fetchone()[0]
    return existing_user_count > 0

def hash_password(password: str) -> str:
    bytes_password = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes_password, salt)
    return hashed_password.decode("utf-8")

def insert_user(cursor, username: str, password: str) -> None:
    query = "INSERT INTO [User] (Id, username, password) VALUES (?, ?, ?);"
    cursor.execute("SELECT COUNT(Id) FROM [User]")
    results = [item[0] for item in cursor.fetchall()]
    cursor.execute(query, (results[0] + 1, username, password))


@app.post("/login")
async def login(data: LoginData) -> dict:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT Id, password FROM [User] WHERE username = ?",
            (data.username,)
        )
        row = cursor.fetchone()
        
        if row:
            stored_password = row.password
            is_password_match = bcrypt.checkpw(
                data.password.encode("utf-8"), stored_password.encode("utf-8")
            )
            if is_password_match:
                cursor.execute(
                    "SELECT * FROM UserDetail WHERE Id = ?",
                    (row.Id,)
                )
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return {"message": "Login Success", "data": results}
            else:
                return {"message": "Username or Password does not match"}
        else:
            return {"message": "Login Fail"}
    except pyodbc.Error as e:
        print(f"Error during login: {e}")
        return {"message": "An error occurred during login"}
    finally:
        cursor.close()
        conn.close()