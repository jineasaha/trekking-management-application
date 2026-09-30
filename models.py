from datetime import date
from flask_login import UserMixin

from extensions import db

# TREK <-> STAFF ASSOCIATION TABLE

trek_staff = db.Table(
    "trek_staff",

    db.Column(
        "trek_id",
        db.Integer,
        db.ForeignKey("treks.trek_id", ondelete="CASCADE"),
        primary_key=True
    ),

    db.Column(
        "staff_id",
        db.Integer,
        db.ForeignKey("staff_profiles.staff_id", ondelete="CASCADE"),
        primary_key=True
    )
)

# USER TABLE 

class User(UserMixin, db.Model):

    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(15)
    )
    
    full_name = db.Column(
    db.String(150)
    )

    date_of_birth = db.Column(
        db.Date
    )

    gender = db.Column(
        db.String(20)
    )

    address = db.Column(
        db.Text
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    is_approved = db.Column(
        db.Boolean,
        default=False
    )

    is_blacklisted = db.Column(
        db.Boolean,
        default=False
    )
    
    def get_id(self):
        return str(self.user_id)

    bookings = db.relationship(
        "Booking",
        backref="user",
        lazy=True
    )

    staff_profile = db.relationship(
        "StaffProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )



# STAFF PROFILE
class StaffProfile(db.Model):

    __tablename__ = "staff_profiles"

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    experience = db.Column(
        db.Integer
    )

    emergency_contact = db.Column(
        db.String(15)
    )
    
    address = db.Column(
    db.String(200)
    )

    user = db.relationship(
        "User",
        back_populates="staff_profile"
    )

    assigned_treks = db.relationship(
        "Trek",
        secondary=trek_staff,
        back_populates="assigned_staff",
        lazy=True
    )

# TREK TABLE 

class Trek(db.Model):

    __tablename__ = "treks"

    trek_id = db.Column(
        db.Integer,
        primary_key=True
    )

    trek_name = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=False
    )

    difficulty = db.Column(
        db.String(30),
        nullable=False
    )

    duration = db.Column(
        db.Integer,
        nullable=False
    )

    available_slots = db.Column(
        db.Integer,
        nullable=False
    )
    
    price = db.Column(
    db.Float,
    nullable=False,
    default=0
    )

    description = db.Column(
        db.Text
    )

    start_date = db.Column(
        db.Date
    )

    end_date = db.Column(
        db.Date
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    assigned_staff = db.relationship(
        "StaffProfile",
        secondary=trek_staff,
        back_populates="assigned_treks",
        lazy=True
    )

    bookings = db.relationship(
        "Booking",
        backref="trek",
        lazy=True
    )


# BOOKING TABLE

class Booking(db.Model):

    __tablename__ = "bookings"

    booking_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    trek_id = db.Column(
        db.Integer,
        db.ForeignKey("treks.trek_id"),
        nullable=False
    )
    
    __table_args__ = (

    db.UniqueConstraint(

        "user_id",
        "trek_id",
        name="unique_booking"

    ),

    )

    booking_date = db.Column(
        db.Date,
        default=date.today
    )

    booking_status = db.Column(
        db.String(20),
        default="Booked"
    )

    payment_status = db.Column(
        db.String(20),
        default="Pending"
    )
    
    participant_confirmed = db.Column(
    db.Boolean,
    default=False
    )
    
    full_name = db.Column(
    db.String(100),
    nullable=False
    )

    age = db.Column(
        db.Integer,
        nullable=False
    )

    gender = db.Column(
        db.String(20),
        nullable=False
    )

    medical_issues = db.Column(
        db.Text,
        default=""
    )

    contact_email = db.Column(
        db.String(100),
        nullable=False
    )

    contact_phone = db.Column(
        db.String(15),
        nullable=False
    )
    
    feedback = db.relationship(
    "Feedback",
    backref="booking",
    uselist=False,
    cascade="all, delete-orphan"
    )
    
    
# FEEDBACK TABLE

class Feedback(db.Model):

    __tablename__ = "feedback"

    feedback_id = db.Column(
        db.Integer,
        primary_key=True
    )

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.booking_id"),
        unique=True,
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comments = db.Column(
        db.Text
    )

    feedback_date = db.Column(
        db.Date,
        default=date.today
    )

    
# PAYMENT SETTINGS TABLE
class PaymentSettings(db.Model):

    __tablename__ = "payment_settings"

    setting_id = db.Column(
        db.Integer,
        primary_key=True
    )

    payment_details = db.Column(
        db.Text,
        nullable=False,
        default=""
    )