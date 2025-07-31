from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'employer' or 'jobseeker'

    # Profile fields
    username = db.Column(db.String(150), unique=True, nullable=False)
    full_name = db.Column(db.String(150))
    bio = db.Column(db.Text)
    location = db.Column(db.String(100))

    # Relationships
    jobs = db.relationship('Job', backref='poster', lazy=True, cascade='all, delete', passive_deletes=True)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Theme and display options
    dark_mode = db.Column(db.Boolean, default=False)
    theme = db.Column(db.String(10), default='light')

    # Geolocation
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Time posted
    posted_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    # Relationship with applications
    applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete', passive_deletes=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)

    job_id = db.Column(db.Integer, db.ForeignKey('job.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
