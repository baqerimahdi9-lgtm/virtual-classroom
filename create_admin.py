"""
اسکریپت ساخت کاربران پیش‌فرض
"""
from app import app
from models import db, User
from werkzeug.security import generate_password_hash


def create_users():
    with app.app_context():
        print('=' * 50)
        print('Creating default users...')
        print('=' * 50)

        users = [
            ('admin', 'admin@site.com', 'admin123', 'admin', 'مدیر سیستم'),
            ('teacher', 'teacher@site.com', 'teacher123', 'teacher', 'استاد نمونه'),
            ('student', 'student@site.com', 'student123', 'student', 'دانشجوی نمونه'),
        ]

        for username, email, password, role, full_name in users:
            if User.query.filter_by(username=username).first():
                print(f'{username} already exists')
            else:
                user = User(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                    role=role,
                    full_name=full_name
                )
                db.session.add(user)
                print(f'{username} created -> {username} / {password}')

        db.session.commit()
        print('=' * 50)
        print('All users ready!')


if __name__ == '__main__':
    create_users()