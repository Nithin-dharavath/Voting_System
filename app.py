from fastapi import FastAPI

app = FastAPI()


#rotues

@app.get("/register")
def register():
    return ("register login step - 1")

@app.get("/login")
def login():
    return("step - 2 ")

@app.get("/admin/login")
def admin_login():
    return("step-3")

add role checking 