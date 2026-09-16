"""
اسکریپت ساخت کاربران اولیه
این فایل رو یک بار اجرا می‌کنی تا ادمین، استاد و دانشجوی نمونه ساخته شن
"""
from app import app
from models import db, User
from werkzeug.security import generate_password_hash


def create_users():
    """ساخت کاربران پیش‌فرض"""
    
    with app.app_context():
        print('\n' + '=' * 50)
        print('🔧 شروع ساخت کاربران پیش‌فرض...')
        print('=' * 50 + '\n')
        
        # ==================== ساخت ادمین ====================
        if User.query.filter_by(username='admin').first():
            print('ℹ️  کاربر admin از قبل وجود دارد')
        else:
            admin = User(
                username='admin',
                email='admin@site.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            print('✅ ادمین ساخته شد')
            print('   👤 نام کاربری: admin')
            print('   🔑 رمز عبور: admin123')
        
        # ==================== ساخت استاد نمونه ====================
        if User.query.filter_by(username='teacher').first():
            print('ℹ️  کاربر teacher از قبل وجود دارد')
        else:
            teacher = User(
                username='teacher',
                email='teacher@site.com',
                password=generate_password_hash('teacher123'),
                role='teacher'
            )
            db.session.add(teacher)
            print('✅ استاد ساخته شد')
            print('   👤 نام کاربری: teacher')
            print('   🔑 رمز عبور: teacher123')
        
        # ==================== ساخت دانشجو نمونه ====================
        if User.query.filter_by(username='student').first():
            print('ℹ️  کاربر student از قبل وجود دارد')
        else:
            student = User(
                username='student',
                email='student@site.com',
                password=generate_password_hash('student123'),
                role='student'
            )
            db.session.add(student)
            print('✅ دانشجو ساخته شد')
            print('   👤 نام کاربری: student')
            print('   🔑 رمز عبور: student123')
        
        # ==================== ذخیره در دیتابیس ====================
        db.session.commit()
        
        print('\n' + '=' * 50)
        print('🎉 همه کاربران آماده هستند!')
        print('=' * 50)
        print('\n📋 خلاصه حساب‌ها:')
        print('┌─────────────┬──────────────┬─────────┐')
        print('│ نام کاربری  │ رمز عبور     │ نقش     │')
        print('├─────────────┼──────────────┼─────────┤')
        print('│ admin       │ admin123     │ ادمین   │')
        print('│ teacher     │ teacher123   │ استاد   │')
        print('│ student     │ student123   │ دانشجو  │')
        print('└─────────────┴──────────────┴─────────┘')
        print('\n⚠️  در محیط واقعی، این رمزها را عوض کنید!\n')


if __name__ == '__main__':
    create_users()