"""
مدل‌های دیتابیس
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(200))
    bio = db.Column(db.Text)
    role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    classrooms = db.relationship('Classroom', backref='teacher', lazy=True)
    messages = db.relationship('Message', backref='author', lazy=True)
    files = db.relationship('FileUpload', backref='uploader', lazy=True)
    tickets = db.relationship('Ticket', backref='owner', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Classroom(db.Model):
    __tablename__ = 'classrooms'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    meeting_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    video_type = db.Column(db.String(20))
    cover_image = db.Column(db.String(500))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    start_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship('FileUpload', backref='classroom',
                            lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='classroom',
                               lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='classroom',
                                  lazy=True, cascade='all, delete-orphan')


class Enrollment(db.Model):
    """ثبت‌نام دانشجو در کلاس"""
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'))
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)


class FileUpload(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200))
    original_name = db.Column(db.String(200))
    file_type = db.Column(db.String(20))  # file / video
    file_size = db.Column(db.Integer)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # low / normal / high
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='open')
    reply = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)