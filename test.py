# import bcrypt

# # Function to encrypt a password
# def encrypt_password(password):
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password

# # Function to check if a password matches the stored hashed password
# def check_password(password, hashed_password):
#     return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# # Example usage
# password = "mysecretpassword"

# # Encrypt the password
# hashed_password = encrypt_password(password)

# print(hashed_password)

# # Check if the password matches the stored hashed password
# password_to_check = "mysecretpassword"
# if check_password(password_to_check, hashed_password):
#     print(check_password(password_to_check,hashed_password))
#     print("Password is correct!")
# else:
#     print("Password is incorrect!")
    


import bcrypt
  
# example password
password = 'passwordabc'
  
# converting password to array of bytes
bytes = password.encode('utf-8')
  
# generating the salt
salt = bcrypt.gensalt()
  
# Hashing the password
hash = bcrypt.hashpw(bytes, salt)
  
# Taking user entered password 
userPassword =  'passwordabc'
  
# encoding user password
userBytes = userPassword.encode('utf-8')
  
# checking password
result = bcrypt.checkpw(userBytes, hash)
  
print(result)