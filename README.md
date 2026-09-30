# 🏔️ PeakTrail - Trekking Management System

PeakTrail is a role-based Trekking Management System developed using **Flask**, **SQLAlchemy**, **SQLite**, **Jinja2**, **HTML**, **CSS**, **Bootstrap**, and **JavaScript**. The application streamlines the management of trekking expeditions by providing dedicated portals for **Administrators**, **Trek Staff**, and **Trekkers**, ensuring efficient trek scheduling, staff management, booking management, payment verification, and participant tracking.

---

## Features

### Administrator

- Dashboard with trekking statistics
- Create, update and delete trekking events
- Assign multiple trek staff to a trek
- View and manage all registered trekkers
- Approve or reject trek staff registrations
- Blacklist or unblacklist users and staff
- Manage booking records
- Update payment instructions
- View completed trek history
- View participant lists
- View trek ratings and user feedback

---

### Trek Staff

- Dedicated dashboard
- View assigned treks
- Update trek status
- Update available slots
- Verify participant payments
- View participant details
- Manage ongoing treks
- Mark treks as completed
- View completed trek history
- Update personal profile
- Change password

---

### Trekker (User)

- User registration and login
- Browse available treks
- Search and filter treks
- Book trekking expeditions
- View assigned trek staff
- View payment instructions
- Track booking status
- Cancel upcoming bookings
- View completed treks
- Submit ratings and feedback
- Manage profile
- Change password
- Explore company expedition history

---

## Project Features

- Role-Based Authentication
- Secure Login System
- Admin Approval for Trek Staff
- Trek Booking Management
- Payment Verification Workflow
- Participant Confirmation
- Trek Status Management
- Dynamic Search Functionality
- Trek History Management
- Feedback & Rating System
- Responsive User Interface
- Mobile Friendly Layout

---

## Technology Stack

### Backend

- Python
- Flask
- SQLAlchemy ORM
- SQLite

### Frontend

- HTML5
- CSS3
- Bootstrap 5
- Jinja2 Templates
- JavaScript

---

## Project Structure

```
PeakTrail/
│
├── app.py
├── models.py
├── routes.py
├── create_db.py
├── requirements.txt
│
├── static/
│   ├── css/
│   ├── images/
│   └── javascript/
│
├── templates/
│   ├── admin/
│   ├── staff/
│   ├── user/
│   ├── login.html
│   ├── register.html
│   └── base.html
│
└── database/
```

---

## Database Modules

The application maintains separate database models for:

- Users
- Trek Staff Profiles
- Treks
- Bookings
- Trek Assignments
- Feedback

The models are connected using SQLAlchemy relationships to maintain data consistency.

---

# User Roles

| Role          | Description                               |
| ------------- | ----------------------------------------- |
| Administrator | Manages the complete system               |
| Trek Staff    | Handles assigned treks and participants   |
| Trekker       | Books treks and manages personal bookings |

---

## Main Workflow

### 1. Registration

- Trekker registers and can log in immediately.
- Trek Staff registers and waits for administrator approval.

---

### 2. Administrator

The administrator:

- Approves trek staff
- Creates trekking events
- Assigns trek staff
- Updates payment instructions
- Monitors bookings
- Manages trekkers
- Maintains trek history

---

### 3. Trek Staff

Assigned staff members:

- Manage their assigned treks
- Verify participant payments
- Confirm participants
- Update trek status
- Complete treks

---

### 4. Trekker

Trekkers can:

- Browse available treks
- Book expeditions
- View booking status
- Track payment verification
- Submit feedback after trek completion

---

# Validation Rules

The system includes several business validations:

- Only approved staff can log in.
- Blacklisted users and staff cannot access the system.
- Trek end date cannot be earlier than the start date.
- Staff availability is checked before assignment.
- Multiple staff can be assigned to a trek.
- Users cannot book the same trek twice.
- Bookings are disabled when no slots are available.
- Payment must be verified before participant confirmation.
- Participants can cancel bookings only while bookings remain open.
- Feedback can only be submitted after completing a trek.

---

# Installation

## 1. Clone the repository

```bash
git clone <repository-url>
cd PeakTrail
```

---

## 2. Create a virtual environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Create the database

Run the database initialization script:

```bash
python create_db.py
```

This will create the SQLite database and insert the predefined administrator account.

---

## 5. Start the application

```bash
python app.py
```

---

## 6. Open in browser

```
http://127.0.0.1:5000
```

---

# Default Administrator Account

The administrator account is created automatically when the database is initialized.

Use the credentials defined in **create_db.py** to log in as the administrator.

---

# Developed Using

- Python
- Flask
- SQLAlchemy
- SQLite
- HTML
- CSS
- Bootstrap
- JavaScript
- Jinja2

---

## License

This project was developed for academic purposes as part of **Modern Application Development Project I** course of IIT Madras BS degree
