from pydantic import BaseModel

class RegisterData(BaseModel):
    username : str
    password : str

class LoginData(BaseModel):
    username : str
    password : str

# class InsertProduct(BaseModel):
#     productName : str
#     productCategory : str
#     createBy : int
#     imagePath : str
#     price : int
#     basePrice : str
#     material : list
#     diamond : list
#     gemstone : list

class GetProduct(BaseModel):
    productId : int