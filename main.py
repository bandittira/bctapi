from fastapi import FastAPI, HTTPException, File, UploadFile
from data_models import *
import pyodbc
from data_models import *
import bcrypt
import datetime
import json
from typing import List, Dict
import boto3
from boto3.s3.transfer import TransferConfig

save_path = "D:\\BANCHANGTONG\\APIs\\bctAPIs\\images"

server = "DESKTOP-U71JKDK\\SQLEXPRESS"
database = "banchangtong"
username = ""
password = ""
app = FastAPI()

conn_str = f"Driver={{SQL Server}};Server={server};Database={database};UID={username}"

AWS_BUCKET_NAME = "banchangtong"
AWS_REGION = "ap-southeast-1"


def upload_image_to_s3(file, key):
    s3 = boto3.client("s3", region_name=AWS_REGION)
    transfer_config = TransferConfig(use_threads=False)
    content_type = "image/jpeg"
    extra_args = {"ContentType": content_type}
    s3.upload_fileobj(
        file, AWS_BUCKET_NAME, key, Config=transfer_config, ExtraArgs=extra_args
    )


@app.post("/insertProduct")
async def insert_product(
    productCategory: str,
    productCode: str,
    createBy: int,
    imagePath: str,
    price: int,
    basePrice: str,
    material: list,
    diamond: list,
    gemstone: list,
    file: UploadFile = File(),
):
    time = datetime.datetime.now()

    filename = file.filename
    with open("{0}\\{1}".format(save_path, filename), "wb+") as f:
        f.write(file.file.read())

    if file:
        file.file.seek(0)
        key = f"images/{file.filename}"
        upload_image_to_s3(file.file, key)

    def get_presigned_url(
        key, expiration=3600
    ):  # Expiration time in seconds (default: 1 hour)
        s3 = boto3.client("s3", region_name=AWS_REGION)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": AWS_BUCKET_NAME, "Key": key},
            ExpiresIn=expiration,
        )
        return url

    image_key = "images/${filename}"
    url = get_presigned_url(image_key)
    print(url)

    materialJSON = json.loads(material[0])
    diamondJSON = json.loads(diamond[0])
    gemstoneJSON = json.loads(gemstone[0])
    print(diamondJSON)
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Fetch the latest ProductId based on ProductCategory
        cursor.execute(
            "SELECT TOP 1 ProductId FROM [Product] WHERE ProductCategory = ? ORDER BY Id DESC",
            (productCategory),
        )
        row = cursor.fetchone()

        if row:
            product_id = int(row[0]) + 1
            # Batch insert for Product, ProductDetail, and ProductMaterial

            cursor.executemany(
                "INSERT INTO Product (ProductCode, ProductId, ProductCategory, CreateDate, CreateBy) VALUES (?, ?, ?, ?, ?)",
                [(productCode, product_id, productCategory, time, createBy)],
            )

            cursor.executemany(
                "INSERT INTO ProductDetail (ProductId, ProductCode, ImagePath, Price, BasePrice) VALUES (?, ?, ?, ?, ?)",
                [(product_id, productCode, imagePath, price, basePrice)],
            )

            cursor.executemany(
                "INSERT INTO ProductMaterial (ProductId, ProductCode, MaterialType, MaterialWeight, MaterialPercent) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        product_id,
                        productCode,
                        mat["MaterialType"],
                        float(mat["MaterialWeight"]),
                        float(mat["MaterialPercent"]),
                    )
                    for mat in materialJSON
                ],
            )

            # Batch insert for ProductDiamonds
            if diamondJSON == []:
                print("diamond ว่าง")
            else:
                cursor.executemany(
                    "INSERT INTO ProductDiamonds (ProductId, ProductCode, Carat, Color, Cut, Clarity, Certificated, Amount, CreateDate, CreateBy) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            product_id,
                            productCode,
                            float(dia["Carat"]),
                            int(dia["Color"]),
                            dia["Cut"],
                            dia["Clarity"],
                            dia["Certificated"],
                            int(dia["Amount"]),
                            time,
                            createBy,
                        )
                        for dia in diamondJSON
                    ],
                )

            if gemstoneJSON == []:
                print("gemstone ว่าง")
            else:
                cursor.executemany(
                    "INSERT INTO ProductGems (ProductId, ProductCode Carat, CreateDate, CreateBy, Amount) VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        (
                            product_id,
                            productCode,
                            float(gems["Carat"]),
                            time,
                            createBy,
                            int(gems["Amount"]),
                        )
                        for gems in gemstoneJSON
                    ],
                )

            # Commit the transaction after all insertions are done.
            conn.commit()

            return {
                "message": "Insert Success",
                "data": [{"productCategory": productCategory}],
                "image": url,
            }
        else:
            return {"message": "Insert fail"}

    except pyodbc.Error as e:
        print(f"Error during insert: {e}")
        return {"message": "An error occurred during insert"}

    finally:
        cursor.close()
        conn.close()


def execute_select_query(conn, query: str, params: tuple) -> List[Dict]:
    cursor = conn.cursor()
    cursor.execute(query, params)
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()
    return results


@app.get("/getProduct/{id}/{productCode}")
async def get_product(id: int, productCode: str) -> dict:
    try:
        conn = pyodbc.connect(conn_str)

        product_query = "SELECT ProductCode, ProductId, ProductCategory, CreateDate, CreateBy FROM Product WHERE ProductId = ? AND ProductCode = ?"
        product_detail_query = "SELECT ImagePath, Price, BasePrice FROM ProductDetail WHERE ProductId = ? AND ProductCode = ?"
        product_diamonds_query = "SELECT Carat, Color, Cut, Clarity, Certificated, Amount, CreateDate, CreateBy FROM ProductDiamonds WHERE ProductId = ? AND ProductCode = ?"
        product_gems_query = (
            "SELECT * FROM ProductGems WHERE ProductId = ? AND ProductCode = ?"
        )
        product_materials_query = "SELECT MaterialType, MaterialWeight, MaterialPercent FROM ProductMaterial WHERE ProductId = ? AND ProductCode = ?"

        product_results = execute_select_query(conn, product_query, (id, productCode))
        product_detail_results = execute_select_query(
            conn, product_detail_query, (id, productCode)
        )
        product_diamonds_results = execute_select_query(
            conn, product_diamonds_query, (id, productCode)
        )
        product_gems_results = execute_select_query(
            conn, product_gems_query, (id, productCode)
        )
        product_materials_results = execute_select_query(
            conn, product_materials_query, (id, productCode)
        )

        conn.commit()

        return {
            "message": "Get product detail Success",
            "product": product_results,
            "productDetail": product_detail_results,
            "productDiamonds": product_diamonds_results,
            "productGems": product_gems_results,
            "productMaterials": product_materials_results,
        }

    except pyodbc.Error as e:
        print(f"Error during read: {e}")
        return {"message": "An error occurred during read"}

    finally:
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
            "SELECT Id, password FROM [User] WHERE username = ?", (data.username,)
        )
        row = cursor.fetchone()

        if row:
            stored_password = row.password
            is_password_match = bcrypt.checkpw(
                data.password.encode("utf-8"), stored_password.encode("utf-8")
            )
            if is_password_match:
                cursor.execute("SELECT * FROM UserDetail WHERE Id = ?", (row.Id,))
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
