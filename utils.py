from functools import wraps
from flask import session
from flask import redirect
from flask import url_for
from flask import flash


def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash("Please login first.", "danger")

            return redirect(url_for("main.login"))

        return f(*args, **kwargs)

    return decorated_function



def role_required(role):

    def decorator(f):

        @wraps(f)

        def decorated_function(*args, **kwargs):

            if "user_id" not in session:

                flash("Please login first.", "danger")

                return redirect(url_for("main.login"))

            if session["role"] != role:

                flash("Unauthorized Access!","danger")
                
                if session["role"] == "Admin":

                    return redirect(
                        url_for("main.admin_dashboard")
                    )

                elif session["role"] == "Staff":

                    return redirect(
                        url_for("main.staff_dashboard")
                    )

                elif session["role"] == "User":

                    return redirect(
                        url_for("main.user_dashboard")
                    )

                return redirect(url_for("main.login"))

            return f(*args, **kwargs)

        return decorated_function

    return decorator