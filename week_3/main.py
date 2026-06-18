from fastapi import FastAPI
from model import User

app = FastAPI()


users = [
    User(name = "Ramesh", id = 1),
    User(name = "Suresh", id = 2)
]

@app.get("/")
def Home():
    return ("Welcome to homepage !!!!")

@app.get("/Users")
def Users():
    return users

@app.get("/User/{id}")
def User(id : int):
    for user in users:
        if user.id == id:
            return user
        else:
            return "User Not Found !!!"
    


@app.get("/Products/{id}")
def products(id: int):
    return {"Product id :":id} 