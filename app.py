from auth_middleware import token_required
from models import Nonce, User, Article
import jwt
import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from save_image import save_pic
from validate import validate_book, validate_email_and_password, validate_user
from flask import current_app

load_dotenv()

app = Flask(__name__)
SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
print(SECRET_KEY)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route("/")
def hello():
    return "Hello World!"


@app.route("/users/", methods=["POST"])
def add_user():
    try:

        user = request.json.get('user')

        if not user:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        is_validated = validate_user(**user)
        if is_validated is not True:
            return dict(message='Invalid data', data=None, error=is_validated), 400
        user = User().create(**user)

        if not user:
            return {
                "message": "User already exists",
                "error": "Conflict",
                "data": None
            }, 409
        # token should expire after 24 hrs, we need a nonce
        curr_nonce = Nonce().curr_nonce(user["email"])
        user["token"] = jwt.encode(
            {"email": user["email"], "nonce": curr_nonce},
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        user.pop("_id")
        return {
            "user": user
        }, 201
    except Exception as e:
        return {
            "message": "Something went wrong",
            "error": str(e),
            "data": None
        }, 500


@app.route("/users/login", methods=["POST"])
def login():
    try:
        data = request.json.get('user')

        if not data:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        # validate input

        is_validated = validate_email_and_password(
            data.get('email'), data.get('password'))

        if is_validated is not True:
            return dict(message='Invalid data', data=None, error=is_validated), 400
        user = User().login(
            data["email"],
            data["password"]
        )

        if user:
            try:

                curr_nonce = Nonce().curr_nonce(user["email"])

                user["token"] = jwt.encode(
                    {"email": user["email"], "nonce": curr_nonce},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )

                user.pop("_id")
                return {
                    "user": user
                }
            except Exception as e:
                return {
                    "error": "Something went wrong",
                    "message": str(e)
                }, 500
        return {
            "message": "Error fetching auth token!, invalid email or password",
            "data": None,
            "error": "Unauthorized"
        }, 404
    except Exception as e:
        return {
            "message": "Something went wrong!",
            "error": str(e),
            "data": None
        }, 500


@app.route("/user/", methods=["GET"])
@token_required
def get_current_user(current_user):
    if "Authorization" in request.headers:
        token = request.headers["Authorization"].split(" ")[1]
    current_user["token"] = token
    return jsonify({
        "user": current_user
    })


@app.route("/user/", methods=["PUT"])
@token_required
def update_user(current_user):
    try:
        user = request.json.get('user')

        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        data = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

        updated_user = User().update(user, data["email"])
        updated_user["token"] = token
        return jsonify({
            "user": updated_user
        }), 201

    except Exception as e:
        return jsonify({
            "message": "failed to update account",
            "error": str(e),
            "data": None
        }), 400


@app.route("/user/", methods=["DELETE"])
@token_required
def disable_user(current_user):
    try:
        User().disable_account(current_user["_id"])
        return jsonify({
            "message": "successfully disabled acount",
            "data": None
        }), 204
    except Exception as e:
        return jsonify({
            "message": "failed to disable account",
            "error": str(e),
            "data": None
        }), 400


@app.route("/logoff/", methods=["POST"])
@token_required
def logoff_user(current_user):
    try:
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        data = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        User().logoff(data["email"])
        return jsonify({
            "message": "successfully logged off",
            "data": None
        }), 201
    except Exception as e:
        return jsonify({
            "message": "failed to disable account",
            "error": str(e),
            "data": None
        }), 400

# ************************************************************************************


@app.route("/nonce/", methods=["POST"])
def add_nonce(email):
    try:

        Nonce().create(email)
        return {
            "message": "Successfully reset nonce"

        }, 201
    except Exception as e:
        return {
            "message": "Something went wrong",
            "error": str(e),
            "data": None
        }, 500


@app.route("/nonce/increment", methods=["POST"])
def increment_nonce():
    try:
        Nonce().update()
        return {
            "message": "Successfully incremented nonce"

        }, 201
    except Exception as e:
        return {
            "message": "Something went wrong",
            "error": str(e),
            "data": None
        }, 500


@app.route("/nonce/reset", methods=["POST"])
def reset_nonce():
    try:
        Nonce().reset()
        return {
            "message": "Successfully reset nonce"

        }, 201
    except Exception as e:
        return {
            "message": "Something went wrong",
            "error": str(e),
            "data": None
        }, 500
# ************************************************************************************


@app.route("/articles/", methods=["POST"])
def add_article():
    try:
        article = request.json

        article = Article().create(**article)
        if not article:
            return {
                "message": "article already exists",
                "error": "Conflict",
                "data": None
            }, 409
        return {
            "message": "Successfully created new article",
            "data": article
        }, 201
    except Exception as e:
        return {
            "message": "Something went wrong",
            "error": str(e),
            "data": None
        }, 500


@app.errorhandler(403)
def forbidden(e):
    return jsonify({
        "message": "Forbidden",
        "error": str(e),
        "data": None
    }), 403


@app.errorhandler(404)
def forbidden(e):
    return jsonify({
        "message": "Endpoint Not Found",
        "error": str(e),
        "data": None
    }), 404


if __name__ == "__main__":
    app.run(debug=True)
