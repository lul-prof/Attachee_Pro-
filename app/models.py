from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import enum
import os
import secrets


# Role-based access control
class UserRole(enum.Enum):
    ATTACHEE = 'attachee'
    ASSESSOR = 'assessor'
    ORG_MANAGER = 'org_manager'
    ADMIN = 'admin'


# Status enums
class LogbookStatus(enum.Enum):
    DRAFT = 'draft'
    SUBMITTED = 'submitted'
    ORG_APPROVED = 'org_approved'
    ORG_REJECTED = 'org_rejected'
    ASSESSOR_APPROVED = 'assessor_approved'
    ASSESSOR_REJECTED = 'assessor_rejected'


class VideoSessionStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


# Association tables for many-to-many relationships
assessor_attachee = db.Table('assessor_attachee',
    db.Column('assessor_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('attachee_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Enum(UserRole), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    organization = db.relationship('Organization', back_populates='users')
    attachee_profile = db.relationship('AttacheeProfile', back_populates='user', uselist=False)
    logbook_entries = db.relationship('LogbookEntry', back_populates='attachee', foreign_keys='LogbookEntry.attachee_id')
    file_uploads = db.relationship('FileUpload', back_populates='attachee')
    notifications = db.relationship('Notification', back_populates='user')
    
    # For assessors: attachees they supervise
    supervised_attachees = db.relationship(
        'User',
        secondary=assessor_attachee,
        primaryjoin=(id == assessor_attachee.c.assessor_id),
        secondaryjoin=(id == assessor_attachee.c.attachee_id),
        backref=db.backref('assessors', lazy='dynamic')
    )
    
    # Video sessions
    initiated_sessions = db.relationship('VideoSession', foreign_keys='VideoSession.attachee_id', back_populates='attachee')
    received_sessions = db.relationship('VideoSession', foreign_keys='VideoSession.assessor_id', back_populates='assessor')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_assessor(self):
        return self.role == UserRole.ASSESSOR
    
    def is_org_manager(self):
        return self.role == UserRole.ORG_MANAGER
    
    def is_attachee(self):
        return self.role == UserRole.ATTACHEE
    
    def __repr__(self):
        return f'<User {self.name}, {self.role.value}>'


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    contact_email = db.Column(db.String(120), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(100), nullable=True)
    industry = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', back_populates='organization')
    
    def __repr__(self):
        return f'<Organization {self.name}>'


class AttacheeProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    university = db.Column(db.String(100), nullable=True)
    course = db.Column(db.String(100), nullable=True)
    year_of_study = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    department = db.Column(db.String(100), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_picture = db.Column(db.String(100), nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='attachee_profile')
    
    def __repr__(self):
        return f'<AttacheeProfile {self.user.name}, {self.course}>'


class LogbookEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attachee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    tasks = db.Column(db.Text, nullable=False)
    skills_gained = db.Column(db.Text, nullable=False)
    challenges = db.Column(db.Text, nullable=True)
    hours_worked = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(LogbookStatus), default=LogbookStatus.DRAFT)
    org_feedback = db.Column(db.Text, nullable=True)
    org_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    org_approved_at = db.Column(db.DateTime, nullable=True)
    assessor_feedback = db.Column(db.Text, nullable=True)
    assessor_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    assessor_approved_at = db.Column(db.DateTime, nullable=True)
    grade = db.Column(db.String(2), nullable=True)  # A, B, C, D, F
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attachee = db.relationship('User', foreign_keys=[attachee_id], back_populates='logbook_entries')
    org_approver = db.relationship('User', foreign_keys=[org_approved_by])
    assessor_approver = db.relationship('User', foreign_keys=[assessor_approved_by])
    
    def __repr__(self):
        return f'<LogbookEntry Week {self.week_number}, {self.attachee.name}, Status: {self.status.value}>'


def generate_unique_filename(filename):
    """Generate a unique filename while preserving the original extension."""
    ext = os.path.splitext(filename)[1]
    return f"{secrets.token_hex(8)}{ext}"


class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attachee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    original_filename = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # e.g., 'report', 'certificate', 'other'
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    description = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attachee = db.relationship('User', back_populates='file_uploads')
    
    def __repr__(self):
        return f'<FileUpload {self.original_filename}, {self.attachee.name}>'


class VideoSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attachee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assessor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(VideoSessionStatus), default=VideoSessionStatus.SCHEDULED)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attachee = db.relationship('User', foreign_keys=[attachee_id], back_populates='initiated_sessions')
    assessor = db.relationship('User', foreign_keys=[assessor_id], back_populates='received_sessions')
    
    def __repr__(self):
        return f'<VideoSession {self.title}, {self.start_time}, Status: {self.status.value}>'


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)  # Optional link to relevant page
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='notifications')
    
    def __repr__(self):
        return f'<Notification {self.title}, for {self.user.name}, Read: {self.is_read}>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    
    def __repr__(self):
        return f'<Message {self.subject}, From: {self.sender.name}, To: {self.recipient.name}>'


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=True)  # If null, it's a global announcement
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    author = db.relationship('User')
    organization = db.relationship('Organization')
    
    def __repr__(self):
        return f'<Announcement {self.title}, Active: {self.is_active}>'