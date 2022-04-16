from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from decouple import config
from flask_cors import CORS, cross_origin

# Prod Or Dev
ENV = config("ENV")

# Getting Production or Development DB Credentials
def env_config():
    if ENV == "DEV":
        URI = config("LOCAL_URI")
        DB_NAME = config("LOCAL_DB_NAME")
        return {"URI": URI, "DB_NAME": DB_NAME}
    if ENV == "PROD":
        URI = config("URI")
        DB_NAME = config("DB_NAME")
        return {"URI": URI, "DB_NAME": DB_NAME}


DB_CREDS = env_config()

# Making a Connection with MongoClient
client = MongoClient(host=DB_CREDS["URI"],connect=False)
# database
db = client[DB_CREDS["DB_NAME"]]
# collection
user = db["users"]

app = Flask(__name__)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# JWT Config
app.config["JWT_SECRET_KEY"] = "OizT0h_e6wDiIBlAX2s"
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@cross_origin()
@app.route("/dashboard")
@jwt_required
def dasboard():
    return jsonify(msg="Welcome!")

@cross_origin(origin='*')
@app.route("/register", methods=["POST"])
def register():
    if request.is_json:
        email = request.json["email"]
        name = request.json["name"]
        password = request.json["password"]
    else:
        email = request.form["email"]
        name = request.form["name"]
        password = request.form["password"]
    
    resp_user = user.find_one({"email": email})
    if resp_user:
        return jsonify(msg="User Already Exist"), 409
    else:
        pw_hash = bcrypt.generate_password_hash(password)
        user_info = dict(name=name, email=email, password=pw_hash, token="")
        user.insert_one(user_info)
        return jsonify(msg="User added sucessfully"), 201

@cross_origin(origin='*')
@app.route("/login", methods=["POST"])
def login():
    if request.is_json:
        email = request.json["email"]
        password = request.json["password"]
    else:
        email = request.form["email"]
        password = request.form["password"]

    resp_user = user.find_one({"email": email})
    if resp_user:
        pass_is_valid = bcrypt.check_password_hash(
            resp_user["password"], password)
        if pass_is_valid:
            access_token = create_access_token(identity=email)
            user.update_one({"email": email}, {
                            "$set": {"token": access_token}})
            return jsonify(msg="Login Succeeded!", accessToken=access_token), 201
        else:
            return jsonify(msg="Password Incorrect"), 401
    else:
        return jsonify(msg="Not Registered"), 401
