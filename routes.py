from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import jsonify
from flask import session
from flask_login import login_user
from flask_login import logout_user

from utils import login_required
from utils import role_required

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

from sqlalchemy import or_

from extensions import db, login_manager
from models import User
from models import Trek
from models import Booking
from models import StaffProfile
from models import Feedback
from models import PaymentSettings

from datetime import datetime

main = Blueprint("main", __name__)

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

def get_available_staff(start_date, end_date, current_trek_id=None):

    all_staff = User.query.filter_by(

        role="Staff",
        is_approved=True,
        is_blacklisted=False

    ).all()

    available_staff = []

    for staff in all_staff:

        profile = staff.staff_profile

        is_available = True

        for trek in profile.assigned_treks:

            if current_trek_id and trek.trek_id == current_trek_id:

                continue

            overlap = (

                start_date <= trek.end_date

                and

                end_date >= trek.start_date

            )

            if overlap:

                is_available = False

                break

        if is_available:

            available_staff.append(staff)

    return available_staff


@main.route("/")
def home():

    return redirect(url_for("main.login"))

@main.route("/register/<role>", methods=["GET", "POST"])
def register(role):

    if role not in ["User", "Staff"]:
        flash("Invalid Registration Type.")
        return redirect(url_for("main.login"))

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if len(name) < 3:

            flash("Name must contain at least 3 characters.")

            return redirect(
                url_for("main.register", role=role)
            )

        if len(password) < 6:

            flash("Password must contain at least 6 characters.")

            return redirect(
                url_for("main.register", role=role)
            )

        if len(phone) != 10 or not phone.isdigit():

            flash("Invalid phone number.")

            return redirect(
                url_for("main.register", role=role)
            )

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("main.register", role=role))

        approved = False if role == "Staff" else True

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            phone=phone,
            role=role,
            is_approved=approved
        )

        db.session.add(new_user)
        db.session.commit()
        
        if role == "Staff":
            profile = StaffProfile(
                staff_id=new_user.user_id
            )

            db.session.add(profile)
            db.session.commit()

        flash("Registration Successful")
        return redirect(url_for("main.login"))

    return render_template("auth/register.html", role=role)

@main.route("/login", methods=["GET", "POST"])
def login():
    
    if "user_id" in session:

        if session["role"] == "Admin":
            return redirect(url_for("main.admin_dashboard"))

        elif session["role"] == "Staff":
            return redirect(url_for("main.staff_dashboard"))

        else:
            return redirect(url_for("main.user_dashboard"))

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user is None:

            flash("User not found!")

            return redirect(url_for("main.login"))

        if not check_password_hash(user.password, password):

            flash("Incorrect Password!")

            return redirect(url_for("main.login"))

        if user.is_blacklisted:

            flash("Your account has been blacklisted.")

            return redirect(url_for("main.login"))

        if user.role == "Staff" and not user.is_approved:

            flash("Waiting for Admin Approval.")

            return redirect(url_for("main.login"))
        
        login_user(user)

        session["user_id"] = user.user_id

        session["role"] = user.role

        session["name"] = user.name

        if user.role == "Admin":

            return redirect(url_for("main.admin_dashboard"))

        elif user.role == "Staff":

            return redirect(url_for("main.staff_dashboard"))

        else:

            return redirect(url_for("main.user_dashboard"))

    return render_template("auth/login.html")

@main.route("/logout")
def logout():
    
    logout_user()

    session.clear()

    flash("Logged out successfully.","success")

    return redirect(url_for("main.login"))

@main.route("/admin")
@role_required("Admin")
def admin_dashboard():

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="User").count()
    total_staff = User.query.filter_by(role="Staff").count()
    total_bookings = Booking.query.count()

    recent_treks = Trek.query.order_by(
        Trek.trek_id.desc()
    ).limit(5).all()

    pending_staff = User.query.filter_by(
        role="Staff",
        is_approved=False
    ).all()

    latest_bookings = Booking.query.order_by(
        Booking.booking_id.desc()
    ).limit(5).all()

    return render_template(

        "admin/admin_dashboard.html",

        name=session["name"],
        total_treks=total_treks,
        total_users=total_users,
        total_staff=total_staff,
        total_bookings=total_bookings,
        recent_treks=recent_treks,
        pending_staff=pending_staff,
        latest_bookings=latest_bookings

    )
    
@main.route("/admin/treks")
@role_required("Admin")
def manage_treks():

    search = request.args.get("search", "").strip()
    staff_id = request.args.get("staff_id", type=int)

    query = Trek.query

    if search:
        query = query.filter(
            (Trek.trek_name.ilike(f"%{search}%")) |
            (Trek.location.ilike(f"%{search}%"))
        )

    if staff_id:
        query = query.filter(
            Trek.assigned_staff.any(
                StaffProfile.staff_id == staff_id
            )
        )

    treks = query.order_by(Trek.trek_id.desc()).all()

    staff_members = User.query.filter_by(
        role="Staff",
        is_approved=True,
        is_blacklisted=False
    ).order_by(User.name).all()
    
    payment_settings = PaymentSettings.query.first()

    return render_template(
        "admin/manage_treks.html",
        name=session["name"],
        treks=treks,
        staff_members=staff_members,
        selected_staff=staff_id,
        payment_details=payment_settings.payment_details if payment_settings else ""
    )
    
@main.route(
    "/admin/payment-details",
    methods=["POST"]
)
@role_required("Admin")
def update_payment_details():

    payment_settings = PaymentSettings.query.first()

    if payment_settings is None:

        payment_settings = PaymentSettings()

        db.session.add(payment_settings)

    payment_settings.payment_details = request.form[
        "payment_details"
    ].strip()

    db.session.commit()

    flash(

        "Payment details updated successfully.",

        "success"

    )

    return redirect(
        url_for("main.manage_treks")
    )

@main.route("/admin/available-staff")
@role_required("Admin")
def available_staff():

    start_date_str = request.args.get("start_date")

    end_date_str = request.args.get("end_date")

    if not start_date_str or not end_date_str:

        return jsonify([])

    start_date = datetime.strptime(
        start_date_str,
        "%Y-%m-%d"
    ).date()

    end_date = datetime.strptime(
        end_date_str,
        "%Y-%m-%d"
    ).date()

    staff_members = get_available_staff(

        start_date,

        end_date

    )

    return jsonify([

        {

            "id": staff.user_id,

            "name": staff.name

        }

        for staff in staff_members

    ])    

@main.route("/admin/treks/add", methods=["GET","POST"])
@role_required("Admin")
def add_trek():

    staff_members = User.query.filter_by(
    role="Staff",
    is_approved=True,
    is_blacklisted=False
    ).all()

    if request.method == "POST":

        assigned_staff_ids = list(set(request.form.getlist("assigned_staff")))
        
        if not request.form["start_date"] or not request.form["end_date"]:

            flash(
                "Please select both dates.",
                "danger"
            )

            return redirect(
                url_for("main.add_trek")
            )
        
        start_date = datetime.strptime(
                            request.form["start_date"],
                            "%Y-%m-%d"
                            ).date()
                    
        end_date = datetime.strptime(
            request.form["end_date"],
            "%Y-%m-%d"
        ).date()
        
        if len(assigned_staff_ids) < 1:
        
                    flash("Assign at least one staff member.", "danger")
        
                    return redirect(url_for("main.add_trek"))
        
        if len(assigned_staff_ids) > 5:

            flash("Maximum 5 staff members can be assigned.", "danger")

            return redirect(url_for("main.add_trek"))

        
        for staff_id in assigned_staff_ids:

            profile = StaffProfile.query.get(int(staff_id))

            for assigned_trek in profile.assigned_treks:

                if (start_date <= assigned_trek.end_date and end_date >= assigned_trek.start_date):

                    flash(

                        f"{profile.user.name} is already assigned "
                        f"to another trek during that period.",

                        "danger"

                    )

                    return redirect(
                        url_for("main.add_trek")
                    )

        duration = (end_date - start_date).days + 1

        if duration <= 0:

            flash(
                "End date must be after start date.",
                "danger"
            )

            return redirect(url_for("main.add_trek"))
        
        slots = int(request.form["available_slots"])

        price = float(request.form["price"])

        if slots < 1:

            flash(
                "Slots must be greater than zero."
            )

            return redirect(
                url_for("main.add_trek")
            )

        if price < 0:

            flash(
                "Price cannot be negative."
            )

            return redirect(
                url_for("main.add_trek")
            )
            
        trek_name = request.form["trek_name"].strip()

        location = request.form["location"].strip()

        existing_trek = Trek.query.filter(

            Trek.trek_name.ilike(trek_name),

            Trek.location.ilike(location),

            Trek.start_date == start_date

        ).first()
        

        if existing_trek:

            flash(
                "This trek already exists."
            )

            return redirect(
                url_for("main.add_trek")
            )

        trek = Trek(

            trek_name=request.form["trek_name"],

            location=request.form["location"],

            difficulty=request.form["difficulty"],

            available_slots=int(
                request.form["available_slots"]
            ),

            price=float(
                request.form["price"]
            ),

            description=request.form["description"],

            start_date=start_date,

            end_date=end_date,

            duration=duration,

            status=request.form["status"]

        )
        
        
        staff_profiles = StaffProfile.query.filter(
            StaffProfile.staff_id.in_(assigned_staff_ids)
        ).all()

        trek.assigned_staff = staff_profiles

        db.session.add(trek)
        db.session.commit()

        flash("Trek added successfully!", "success")

        return redirect(url_for("main.manage_treks"))

    return render_template(
        "admin/add_trek.html",
        staff_members=staff_members
    )
    
@main.route("/admin/treks/<int:trek_id>/available-staff")
@role_required("Admin")
def edit_available_staff(trek_id):

    start_date_str = request.args.get("start_date")

    end_date_str = request.args.get("end_date")

    if not start_date_str:

        return jsonify([])

    start_date = datetime.strptime( start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str,"%Y-%m-%d").date()

    staff_members = get_available_staff(start_date, end_date, current_trek_id=trek_id)

    return jsonify(

        [

            {

                "id": staff.user_id,

                "name": staff.name

            }

            for staff in staff_members

        ]

    )
      
@main.route("/admin/treks/edit/<int:trek_id>", methods=["GET", "POST"])
@role_required("Admin")
def edit_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)
    
    if request.method == "POST" and trek.status in [
        "Trek Ongoing",
        "Completed"
    ]:

        trek.description = request.form.get(
            "description",
            ""
        ).strip()

        db.session.commit()

        flash(
            "Trek description updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.manage_treks")
        )

    staff_members = get_available_staff(

    trek.start_date,

    trek.end_date,

    current_trek_id=trek.trek_id

    )

    selected_staff_ids = [

        profile.staff_id

        for profile in trek.assigned_staff

    ]
   
    if request.method == "POST":
        
        start_date = datetime.strptime(
        request.form["start_date"],
        "%Y-%m-%d"
        ).date()
    
        end_date = datetime.strptime(
            request.form["end_date"],
            "%Y-%m-%d"
        ).date()
    
        duration = (end_date - start_date).days + 1
    
        if duration <= 0:
    
            flash(
                "End date must be after start date.",
                "danger"
            )
    
            return redirect(
                url_for(
                    "main.edit_trek",
                    trek_id=trek.trek_id
                )
            )
            
        slots = int(request.form["available_slots"])

        price = float(request.form["price"])

        if slots < 1:

            flash(
                "Slots must be greater than zero.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.edit_trek",
                    trek_id=trek.trek_id
                )
            )
            
        confirmed_count = Booking.query.filter_by(trek_id=trek_id, participant_confirmed=True).count()
        
        if slots < confirmed_count:
            flash(

                f"Slots cannot be less than "
                f"{confirmed_count} confirmed participants.",

                "danger"

            )
            
            return redirect( url_for(
                "main.edit_trek",
                trek_id=trek_id)
            )

        if price < 0:

            flash(
                "Price cannot be negative.",
                "danger"
            )

            return redirect(
                url_for(
                    "main.edit_trek",
                    trek_id=trek.trek_id
                )
            )
            
        existing_trek = Trek.query.filter(
            Trek.trek_id != trek_id,

            Trek.trek_name.ilike(
                request.form["trek_name"].strip()
            ),

            Trek.location.ilike(
                request.form["location"].strip()
            ),

            Trek.start_date == start_date).first()
        
        if existing_trek:

            flash(
                "Another trek with the same details already exists.",
                "danger"
            )
            
            return redirect( url_for( "main.edit_trek",trek_id=trek_id ) )   
        

        trek.trek_name = request.form["trek_name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = duration
        trek.price=float(request.form["price"])
        trek.description=request.form["description"]
        trek.available_slots = int(request.form["available_slots"])

        trek.start_date = datetime.strptime(
            request.form["start_date"],
            "%Y-%m-%d"
        ).date()

        trek.end_date = datetime.strptime(
            request.form["end_date"],
            "%Y-%m-%d"
        ).date()

        trek.status = request.form["status"]

        assigned_staff_ids = list(set(request.form.getlist("assigned_staff")))
        
        for staff_id in assigned_staff_ids:

            profile = StaffProfile.query.get(int(staff_id))

            for assigned_trek in profile.assigned_treks:

                if assigned_trek.trek_id == trek.trek_id:

                    continue

                if (start_date <= assigned_trek.end_date and end_date >= assigned_trek.start_date):

                    flash(

                        f"{profile.user.name} is already assigned "
                        f"to another trek during that period.",

                        "danger"

                    )

                    return redirect(

                        url_for(

                            "main.edit_trek",

                            trek_id=trek.trek_id

                        )

                    )

        if len(assigned_staff_ids) < 1:

            flash("Assign at least one staff member.", "danger")

            return redirect(
                url_for(
                    "main.edit_trek",
                    trek_id=trek.trek_id
                )
            )

        if len(assigned_staff_ids) > 5:
            flash("Maximum 5 staff members can be assigned.", "danger")

            return redirect(
                url_for(
                    "main.edit_trek",
                    trek_id=trek.trek_id
                )
            )

        staff_profiles = StaffProfile.query.filter(
            StaffProfile.staff_id.in_(assigned_staff_ids)
        ).all()

        trek.assigned_staff = staff_profiles

        db.session.commit()

        flash("Trek updated successfully.", "success")

        return redirect(url_for("main.manage_treks"))

    return render_template(

    "admin/edit_trek.html",
    trek=trek,
    staff_members=staff_members,
    selected_staff_ids=selected_staff_ids

    )
       
@main.route("/admin/treks/delete/<int:trek_id>", methods=["POST"])
@role_required("Admin")
def delete_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)
    
    if trek.bookings:

        flash(
            "Cannot delete a trek that has bookings.",
            "danger"
        )
        return redirect(url_for("main.manage_treks"))
    
    db.session.delete(trek)
    db.session.commit()
    flash("Trek Deleted Successfully.")
    return redirect(url_for("main.manage_treks"))

@main.route("/admin/staff")
@role_required("Admin")
def manage_staff():

    search = request.args.get("search")

    query = User.query.filter_by(role="Staff")

    if search:

        query = query.filter(
            (User.name.contains(search)) |
            (User.email.contains(search))
        )

    staff = query.order_by(User.name).all()

    return render_template(
        "admin/manage_staff.html",
        name=session["name"],
        staff=staff
    )
    
@main.route("/admin/staff/approve/<int:staff_id>")
@role_required("Admin")
def approve_staff(staff_id):

    staff = User.query.get_or_404(staff_id)

    staff.is_approved = True

    db.session.commit()

    flash("Staff approved successfully.", "success")

    return redirect(url_for("main.manage_staff"))

@main.route("/admin/staff/reject/<int:staff_id>", methods=["POST"])
@role_required("Admin")
def reject_staff(staff_id):

    staff = User.query.get_or_404(staff_id)

    profile = staff.staff_profile

    if profile:
        db.session.delete(profile)

    db.session.delete(staff)

    db.session.commit()

    flash(
        "Staff registration rejected successfully.",
        "success"
    )

    return redirect(
        url_for("main.manage_staff")
    )

@main.route("/admin/staff/remove/<int:staff_id>", methods=["POST"])
@role_required("Admin")
def remove_staff(staff_id):

    staff = User.query.get_or_404(staff_id)

    profile = staff.staff_profile

    if profile and profile.assigned_treks:

        flash(
            "This staff is assigned to one or more treks. "
            "Reassign or remove them from those treks first.",
            "danger"
        )

        return redirect(
            url_for("main.manage_staff")
        )

    if profile:
        db.session.delete(profile)

    db.session.delete(staff)

    db.session.commit()

    flash(
        "Staff removed successfully.",
        "success"
    )

    return redirect(
        url_for("main.manage_staff")
    )

@main.route("/admin/staff/blacklist/<int:staff_id>", methods=["POST"])
@role_required("Admin")
def blacklist_staff(staff_id):

    staff = User.query.get_or_404(staff_id)

    staff.is_blacklisted = True

    db.session.commit()

    flash("Staff blacklisted.", "warning")

    return redirect(url_for("main.manage_staff"))

@main.route("/admin/staff/unblacklist/<int:staff_id>")
@role_required("Admin")
def unblacklist_staff(staff_id):

    staff = User.query.get_or_404(staff_id)

    staff.is_blacklisted = False

    db.session.commit()

    flash("Staff restored successfully.", "success")

    return redirect(url_for("main.manage_staff"))


@main.route("/admin/users")
@role_required("Admin")
def manage_users():

    search = request.args.get("search")

    query = User.query.filter_by(role="User")

    if search:

        query = query.filter(
            (User.name.contains(search)) |
            (User.email.contains(search))
        )

    users = query.order_by(User.name).all()

    return render_template(
        "admin/manage_users.html",
        name=session["name"],
        users=users
    )
    
@main.route("/admin/users/blacklist/<int:user_id>", methods=['POST'])
@role_required("Admin")
def blacklist_user(user_id):

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = True

    db.session.commit()

    flash("User blacklisted successfully.", "warning")

    return redirect(url_for("main.manage_users"))


@main.route("/admin/users/unblacklist/<int:user_id>")
@role_required("Admin")
def unblacklist_user(user_id):

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = False

    db.session.commit()

    flash("User restored successfully.", "success")

    return redirect(url_for("main.manage_users"))
    

@main.route("/admin/bookings")
@role_required("Admin")
def booking_records():

    search = request.args.get("search", "").strip()

    query = Booking.query

    if search:

        query = query.join(User).join(Trek).filter(

            or_(

                User.name.ilike(f"%{search}%"),

                Trek.trek_name.ilike(f"%{search}%")

            )

        )

    bookings = query.order_by(
        Booking.booking_date.desc()
    ).all()

    return render_template(

        "admin/bookings.html",

        bookings=bookings

    )

@main.route("/admin/history")
@role_required("Admin")
def trek_history():

    treks = Trek.query.filter_by(
        status="Completed"
    ).order_by(
        Trek.start_date.desc()
    ).all()

    return render_template(
        "admin/history.html",
        name=session["name"],
        treks=treks
    )

@main.route("/staff")
@role_required("Staff")
def staff_dashboard():

    staff = StaffProfile.query.get_or_404(
        session["user_id"]
    )

    assigned_treks = staff.assigned_treks
    
    bookings_open = len([
    trek
    for trek in assigned_treks
    if trek.status == "Bookings Open"
    ])

    active_treks = 0

    completed_treks = 0

    total_participants = 0

    for trek in assigned_treks:

        if trek.status == "Trek Ongoing":

            active_treks += 1

        elif trek.status == "Completed":

            completed_treks += 1

        for booking in trek.bookings:

            if (
                booking.payment_status == "Completed"
                and booking.participant_confirmed
            ):

                total_participants += 1

    return render_template(

        "staff/staff_dashboard.html",

        name=session["name"],

        assigned_treks=assigned_treks,
        
        bookings_open=bookings_open,

        active_treks=active_treks,

        completed_treks=completed_treks,

        total_participants=total_participants

    )
    
   
@main.route("/staff/treks")
@role_required("Staff")
def staff_treks():

    staff = StaffProfile.query.get_or_404(
        session["user_id"]
    )

    return render_template(

        "staff/staff_treks.html",

        name=session["name"],

        assigned_treks=staff.assigned_treks

    )


@main.route("/staff/treks/ongoing")
@role_required("Staff")
def staff_ongoing_treks():

    staff = StaffProfile.query.get_or_404(
        session["user_id"]
    )

    ongoing_treks = [

        trek

        for trek in staff.assigned_treks

        if trek.status == "Trek Ongoing"

    ]

    return render_template(

        "staff/staff_ongoing_treks.html",

        name=session["name"],

        ongoing_treks=ongoing_treks

    )
  

@main.route("/staff/treks/completed")
@role_required("Staff")
def staff_completed_treks():

    staff = StaffProfile.query.get_or_404(
        session["user_id"]
    )

    completed_treks = [

        trek

        for trek in staff.assigned_treks

        if trek.status == "Completed"

    ]

    return render_template(

        "staff/staff_completed_treks.html",

        name=session["name"],

        completed_treks=completed_treks

    )

@main.route("/staff/profile", methods=["GET", "POST"])
@role_required("Staff")
def staff_profile():

    user = User.query.get_or_404(session["user_id"])

    profile = user.staff_profile

    if request.method == "POST":

        user.name = request.form["name"]

        user.phone = request.form["phone"]

        profile.experience = int(request.form["experience"]) if request.form["experience"] else None

        profile.emergency_contact = request.form["emergency_contact"]

        profile.address = request.form["address"]

        db.session.commit()

        session["name"] = user.name

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.staff_profile")
        )

    assigned_count = len(profile.assigned_treks)

    ongoing_count = len([
        trek
        for trek in profile.assigned_treks
        if trek.status == "Trek Ongoing"
    ])

    bookings_open = len([
        trek
        for trek in profile.assigned_treks
        if trek.status == "Bookings Open"
        ])

    completed_count = len([
        trek
        for trek in profile.assigned_treks
        if trek.status == "Completed"
    ])

    participant_count = 0

    for trek in profile.assigned_treks:

        participant_count += len([
            booking
            for booking in trek.bookings
            if booking.payment_status == "Completed"
            and booking.participant_confirmed
        ])

    return render_template(

        "staff/staff_profile.html",

        name=session["name"],

        current_user=user,

        assigned_count=assigned_count,
        
        bookings_open = bookings_open,

        ongoing_count=ongoing_count,

        completed_count=completed_count,

        participant_count=participant_count

    )

@main.route("/staff/change-password", methods=["POST"])
@role_required("Staff")
def staff_change_password():

    user = User.query.get_or_404(
        session["user_id"]
    )

    current_password = request.form["current_password"]

    new_password = request.form["new_password"]

    confirm_password = request.form["confirm_password"]

    if not check_password_hash(
        user.password,
        current_password
    ):

        flash(
            "Current password is incorrect.",
            "danger"
        )

        return redirect(
            url_for("main.staff_profile")
        )

    if new_password != confirm_password:

        flash(
            "Passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("main.staff_profile")
        )

    user.password = generate_password_hash(
        new_password
    )

    db.session.commit()

    flash(
        "Password changed successfully.",
        "success"
    )

    return redirect(
        url_for("main.staff_profile")
    )
    
@main.route("/staff/trek/<int:trek_id>/participants")
@role_required("Staff")
def staff_trek_participants(trek_id):

    staff = StaffProfile.query.get_or_404(session["user_id"])

    trek = Trek.query.get_or_404(trek_id)

    if trek not in staff.assigned_treks:

        flash("Unauthorized access.", "danger")

        return redirect(url_for("main.staff_treks"))

    bookings = Booking.query.filter_by(
    trek_id=trek_id
    ).order_by(
        Booking.booking_date
    ).all()

    return render_template(

        "staff/staff_participants.html",

        name=session["name"],

        trek=trek,

        bookings=bookings

    )
    
@main.route("/staff/ongoing-trek/<int:trek_id>/participants")
@role_required("Staff")
def staff_ongoing_participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    
    staff = StaffProfile.query.get_or_404(
    session["user_id"]
    )

    if trek not in staff.assigned_treks:

        flash("Unauthorized access.","danger")

        return redirect(
            url_for("main.staff_treks")
        )

    

    bookings = trek.bookings

    return render_template(

        "staff/staff_participants.html",

        trek=trek,

        bookings=bookings,

        source="ongoing"

    )


@main.route("/staff/completed-trek/<int:trek_id>/participants")
@role_required("Staff")
def staff_completed_participants(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    
    staff = StaffProfile.query.get_or_404(
    session["user_id"]
    )

    if trek not in staff.assigned_treks:

        flash("Unauthorized access.","danger")

        return redirect(
            url_for("main.staff_treks")
        )

    

    bookings = trek.bookings

    return render_template(

        "staff/staff_participants.html",

        trek=trek,

        bookings=bookings,

        source="completed"

    )
    
@main.route(
    "/staff/payment/<int:booking_id>",
    methods=["POST"]
)
@role_required("Staff")
def update_payment_status(booking_id):

    booking = Booking.query.get_or_404(booking_id)

    staff = StaffProfile.query.get_or_404(
        session["user_id"]
    )

    if booking.trek not in staff.assigned_treks:

        flash("Unauthorized access.","danger")

        return redirect(
            url_for("main.staff_treks")
        )

    new_status = request.form["payment_status"]

    booking.payment_status = new_status

    if new_status == "Completed":

        booking.participant_confirmed = True

    else:

        booking.participant_confirmed = False

    db.session.commit()

    flash(
        "Payment updated successfully."
    )

    return redirect(

        url_for(

            "main.staff_trek_participants",

            trek_id=booking.trek_id

        )

    )
    
@main.route(
    "/staff/participant/confirm/<int:booking_id>",
    methods=["POST"]
)
@role_required("Staff")
def confirm_participant(booking_id):

    booking = Booking.query.get_or_404(booking_id)

    staff = StaffProfile.query.get_or_404(session["user_id"])

    if booking.trek not in staff.assigned_treks:

        flash("Unauthorized action.", "danger")

        return redirect(url_for("main.staff_treks"))

    if booking.payment_status != "Completed":

        flash(
            "Participant payment is not completed.",
            "warning"
        )

        return redirect(
            url_for(
                "main.staff_trek_participants",
                trek_id=booking.trek_id
            )
        )

    booking.participant_confirmed = True

    db.session.commit()

    flash(
        "Participant confirmed successfully.",
        "success"
    )

    return redirect(
        url_for(
            "main.staff_trek_participants",
            trek_id=booking.trek_id
        )
    )
    
@main.route(
    "/staff/participant/remove/<int:booking_id>",
    methods=["POST"]
)
@role_required("Staff")
def remove_participant(booking_id):

    booking = Booking.query.get_or_404(booking_id)

    staff = StaffProfile.query.get_or_404(session["user_id"])

    if booking.trek not in staff.assigned_treks:

        flash("Unauthorized action.", "danger")

        return redirect(url_for("main.staff_treks"))

    booking.participant_confirmed = False

    db.session.commit()

    flash(
        "Participant removed successfully.",
        "success"
    )

    return redirect(
        url_for(
            "main.staff_trek_participants",
            trek_id=booking.trek_id
        )
    )
    
@main.route(
    "/staff/trek/update/<int:trek_id>",
    methods=["GET", "POST"]
)
@role_required("Staff")
def staff_update_trek(trek_id):

    staff = StaffProfile.query.get_or_404(session["user_id"])

    trek = Trek.query.get_or_404(trek_id)

    if trek not in staff.assigned_treks:

        flash("Unauthorized access.", "danger")

        return redirect(url_for("main.staff_treks"))
    
    if request.method == "POST":

        trek.status = request.form["status"]
        
        confirmed_count = sum(
            1 for booking in trek.bookings
            if booking.participant_confirmed)
        
        new_slots = int(request.form["available_slots"])
        
        if new_slots < 1:
            flash("Slots must be greater than zero.","danger")
            return redirect(url_for("main.staff_update_trek",trek_id=trek.trek_id))
    
        if new_slots < confirmed_count:
    
            flash(
                f"Slots cannot be less than "
                f"{confirmed_count} confirmed participants.",
                "danger"
            )
    
            return redirect(
                url_for(
                    "main.staff_update_trek",
                    trek_id=trek.trek_id
                )
            )

        trek.available_slots = new_slots

        db.session.commit()

        flash(
            "Trek updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.staff_treks")
        )

    return render_template(

        "staff/staff_update_trek.html",

        name=session["name"],

        trek=trek

    )
    
@main.route(
    "/staff/trek/complete/<int:trek_id>",
    methods=["POST"]
)
@role_required("Staff")
def staff_complete_trek(trek_id):

    staff = StaffProfile.query.get_or_404(session["user_id"])

    trek = Trek.query.get_or_404(trek_id)

    if trek not in staff.assigned_treks:

        flash("Unauthorized action.", "danger")

        return redirect(url_for("main.staff_ongoing_treks"))

    trek.status = "Completed"

    db.session.commit()

    flash(
        "Trek marked as completed.",
        "success"
    )

    return redirect(url_for("main.staff_completed_treks"))

@main.route("/user")
@role_required("User")
def user_dashboard():

    bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    booked_count = len(bookings)

    upcoming_count = len([
        b for b in bookings
        if b.trek.status == "Bookings Open"
    ])

    ongoing_count = len([
        b for b in bookings
        if b.trek.status == "Trek Ongoing"
    ])

    completed_count = len([
        b for b in bookings
        if b.trek.status == "Completed"
    ])

    recent_bookings = bookings[-5:]

    return render_template(

        "user/user_dashboard.html",
        
        name=session["name"],

        booked_count=booked_count,

        upcoming_count=upcoming_count,

        ongoing_count=ongoing_count,

        completed_count=completed_count,

        recent_bookings=recent_bookings

    )
    
@main.route("/user/treks")
@role_required("User")
def available_treks():

    search = request.args.get("search", "")
    difficulty = request.args.get("difficulty", "")

    treks = Trek.query.filter(
        Trek.status == "Bookings Open"
    )

    if search:

        treks = treks.filter(

            db.or_(

                Trek.trek_name.ilike(f"%{search}%"),

                Trek.location.ilike(f"%{search}%")
            )
        )

    if difficulty:

        treks = treks.filter(

            Trek.difficulty == difficulty
        )

    treks = treks.order_by(Trek.start_date.asc()).all()
    
    booked_trek_ids = [

    booking.trek_id

    for booking in Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    ]
    
    payment_settings = PaymentSettings.query.first()

    return render_template(

        "user/available_treks.html",
        treks=treks,
        search=search,
        difficulty=difficulty,
        booked_trek_ids=booked_trek_ids,
        payment_details=payment_settings.payment_details if payment_settings else ""
    )
   
@main.route("/user/book/<int:trek_id>", methods=["POST"])
@role_required("User")
def book_trek(trek_id):

    trek = Trek.query.get_or_404(trek_id)

    existing = Booking.query.filter_by(

        user_id=session["user_id"],

        trek_id=trek_id

    ).first()

    if existing:

        flash("Already booked.","warning")

        return redirect(
            url_for("main.available_treks")
        )

    if trek.status != "Bookings Open":

        flash("Bookings are closed.")

        return redirect(
            url_for("main.available_treks")
        )

    confirmed = Booking.query.filter_by(

    trek_id=trek_id,

    participant_confirmed=True

    ).count()

    if confirmed >= trek.available_slots:

        flash("Slots are full.")

        return redirect(
            url_for("main.available_treks")
        )

    user = User.query.get(session["user_id"])

    same_contact = request.form.get("same_contact")

    if same_contact == "yes":

        email = user.email
        phone = user.phone

    else:

        email = request.form["contact_email"]
        phone = request.form["contact_phone"]
        if len(phone) != 10 or not phone.isdigit():

            flash(
                "Invalid phone number."
            )

            return redirect(
                url_for("main.available_treks")
            )
            
    full_name = request.form["full_name"].strip()
        
    if len(full_name) < 3:

        flash(
            "Invalid full name."
        )

        return redirect(
            url_for("main.available_treks")
        )

    booking = Booking(

        user_id=session["user_id"],

        trek_id=trek_id,

        full_name=request.form["full_name"],

        age=int(request.form["age"]),

        gender=request.form["gender"],

        medical_issues=request.form["medical_issues"],

        contact_email=email,

        contact_phone=phone
    )
    

    db.session.add(booking)

    db.session.commit()

    flash("Booking successful.","success")

    return redirect(
        url_for("main.my_bookings")
    )
    
@main.route("/user/bookings")
@role_required("User")
def my_bookings():

    bookings = Booking.query.filter_by(

        user_id=session["user_id"]

    ).order_by(

        Booking.booking_date.desc()

    ).all()

    return render_template(

        "user/my_bookings.html",

        bookings=bookings

    )
    
@main.route(
    "/user/cancel-booking/<int:booking_id>",
    methods=["POST"]
)
@role_required("User")
def cancel_booking(booking_id):

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:

        flash(
            "Unauthorized action.",
            "danger"
        )

        return redirect(
            url_for("main.my_bookings")
        )

    trek = booking.trek

    # User can cancel only if bookings are still open

    if trek.status != "Bookings Open":

        flash(
            "This trek can no longer be cancelled.",
            "danger"
        )

        return redirect(
            url_for("main.my_bookings")
        )

    db.session.delete(booking)

    db.session.commit()

    flash(
        "Booking cancelled successfully.",
        "success"
    )

    return redirect(
        url_for("main.my_bookings")
    )
    
@main.route("/user/history")
@role_required("User")
def user_history():

    completed_bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    completed_bookings = [

        booking

        for booking in completed_bookings

        if booking.trek.status == "Completed"

    ]

    return render_template(

        "user/trek_history.html",

        completed_bookings=completed_bookings

    )   
    
@main.route("/user/profile", methods=["GET", "POST"])
@role_required("User")
def user_profile():

    user = User.query.get_or_404(
        session["user_id"]
    )

    if request.method == "POST":

        user.phone = request.form["phone"]

        user.email = request.form["email"]

        user.full_name = request.form["full_name"]

        user.gender = request.form["gender"]

        user.address = request.form["address"]

        dob = request.form["date_of_birth"]

        if dob:

            user.date_of_birth = datetime.strptime(
                dob,
                "%Y-%m-%d"
            ).date()

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.user_profile")
        )
    
    total_bookings = len(user.bookings)

    completed_treks = len([
        booking
        for booking in user.bookings
        if booking.trek.status == "Completed"
    ])

    return render_template(

        "user/user_profile.html",

        current_user=user,

        total_bookings=total_bookings,

        completed_treks=completed_treks
    )
    
@main.route(
    "/user/change-password",
    methods=["POST"]
)
@role_required("User")
def user_change_password():

    user = User.query.get_or_404(
        session["user_id"]
    )

    current_password = request.form[
        "current_password"
    ]

    new_password = request.form[
        "new_password"
    ]

    confirm_password = request.form[
        "confirm_password"
    ]

    if not check_password_hash(
        user.password,
        current_password
    ):

        flash(
            "Current password is incorrect.",
            "danger"
        )

        return redirect(
            url_for("main.user_profile")
        )

    if new_password != confirm_password:

        flash(
            "Passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("main.user_profile")
        )

    user.password = generate_password_hash(
        new_password
    )

    db.session.commit()

    flash(
        "Password changed successfully.",
        "success"
    )

    return redirect(
        url_for("main.user_profile")
    )
    
@main.route("/user/company-treks")
@role_required("User")
def company_treks():

    ongoing_treks = Trek.query.filter_by(
        status="Trek Ongoing"
    ).order_by(
        Trek.start_date.desc()
    ).all()

    completed_treks = Trek.query.filter_by(
        status="Completed"
    ).order_by(
        Trek.start_date.desc()
    ).all()
    
    # Calculate confirmed participants for every trek
    participant_counts = {}

    for trek in ongoing_treks + completed_treks:
        participant_counts[trek.trek_id] = Booking.query.filter_by(
            trek_id=trek.trek_id,
            participant_confirmed=True
        ).count()

    return render_template(

        "user/company_treks.html",

        ongoing_treks=ongoing_treks,

        completed_treks=completed_treks,
        participant_counts=participant_counts

    )
    
@main.route("/user/feedback/<int:booking_id>", methods=["POST"])
@role_required("User")
def give_feedback(booking_id):

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:

        flash("Unauthorized access.", "danger")

        return redirect(url_for("main.user_history"))

    if booking.feedback:

        flash("You have already submitted feedback.", "warning")

        return redirect(url_for("main.user_history"))

    if request.method == "POST":

        feedback = Feedback(

            booking_id=booking.booking_id,

            rating=int(request.form["rating"]),

            comments=request.form["comments"]

        )

        db.session.add(feedback)

        db.session.commit()

        flash("Thank you for your feedback!", "success")

        return redirect(url_for("main.user_history"))

    return render_template(
        "user/feedback.html",
        booking=booking
    )