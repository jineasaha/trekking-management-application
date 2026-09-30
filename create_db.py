from app import app
from extensions import db
from models import User, PaymentSettings
from werkzeug.security import generate_password_hash

with app.app_context():

    db.create_all()
    
    if not PaymentSettings.query.first():

        db.session.add(

            PaymentSettings(

                payment_details=""

            )

        )

        db.session.commit()

    admin = User.query.filter_by(email="admin@trek.com").first()

    if admin is None:

        admin = User(
            name="Administrator",
            email="admin@trek.com",
            password=generate_password_hash("admin123"),
            phone="9999999999",
            role="Admin",
            is_approved=True
        )

        db.session.add(admin)
        db.session.commit()

    print("Database created successfully.")