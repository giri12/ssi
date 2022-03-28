from functools import wraps
import jwt
from flask import request, abort
from flask import current_app
import models


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return {
                "message": "Authentication Token is missing!",
                "data": None,
                "error": "Unauthorized"
            }, 401
        try:

            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"])

            curr_nonce = models.Nonce().curr_nonce(data["email"])
            nonce_from_user = data["nonce"]
            if curr_nonce != nonce_from_user:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401
            current_user = models.User().get_by_email(data["email"])
            if current_user is None:
                return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401
            # if not current_user["active"]:
            #     abort(403)
        except Exception as e:
            return {
                "message": "Something went wrong",
                "data": None,
                "error": str(e)
            }, 500
        current_user.pop("password")
        current_user.pop("_id")
        return f(current_user, *args, **kwargs)

    return decorated
