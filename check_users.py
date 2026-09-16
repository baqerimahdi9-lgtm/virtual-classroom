"""
اسکریپت بررسی کاربران دیتابیس
این فایل رو اجرا کن تا ببینی چه کاربرانی توی دیتابیس هستن
"""
from app import app
from models import db, User, Classroom, FileUpload, Message, Ticket


def check_database():
    """بررسی کامل دیتابیس"""
    
    with app.app_context():
        print('\n' + '=' * 60)
        print('📊 گزارش کامل دیتابیس')
        print('=' * 60 + '\n')
        
        # ==================== کاربران ====================
        print('👥 کاربران:')
        print('-' * 60)
        
        users = User.query.all()
        print(f'تعداد کل کاربران: {len(users)}\n')
        
        if users:
            # هدر جدول
            print(f'{"ID":<5} {"نام کاربری":<15} {"ایمیل":<25} {"نقش":<12}')
            print('-' * 60)
            
            for u in users:
                print(f'{u.id:<5} {u.username:<15} {u.email:<25} {u.role:<12}')
        else:
            print('❌ هیچ کاربری وجود ندارد!')
        
        print()
        
        # ==================== کلاس‌ها ====================
        print('📚 کلاس‌ها:')
        print('-' * 60)
        
        classes = Classroom.query.all()
        print(f'تعداد کل کلاس‌ها: {len(classes)}\n')
        
        if classes:
            for c in classes:
                print(f'  📖 {c.title}')
                print(f'     استاد: {c.teacher.username if c.teacher else "نامشخص"}')
                print(f'     لینک: {c.meeting_url}')
                print()
        else:
            print('ℹ️  هنوز کلاسی ساخته نشده.\n')
        
        # ==================== فایل‌ها ====================
        print('📁 فایل‌ها:')
        print('-' * 60)
        
        files = FileUpload.query.all()
        print(f'تعداد کل فایل‌ها: {len(files)}\n')
        
        if files:
            for f in files:
                print(f'  📄 {f.original_name}')
        else:
            print('ℹ️  هنوز فایلی آپلود نشده.\n')
        
        # ==================== پیام‌ها ====================
        print('💬 پیام‌های چت:')
        print('-' * 60)
        
        messages = Message.query.all()
        print(f'تعداد کل پیام‌ها: {len(messages)}\n')
        
        # ==================== تیکت‌ها ====================
        print('🎫 تیکت‌ها:')
        print('-' * 60)
        
        tickets = Ticket.query.all()
        print(f'تعداد کل تیکت‌ها: {len(tickets)}\n')
        
        if tickets:
            for t in tickets:
                print(f'  🎫 {t.subject} — {t.status}')
        
        print('\n' + '=' * 60)
        print('✅ بررسی کامل شد')
        print('=' * 60 + '\n')


if __name__ == '__main__':
    check_database()
    from sqlalchemy import text

with app.app_context():
    # تعداد کاربران
    result = db.session.execute(text('SELECT COUNT(*) FROM users')).scalar()
    print(f'📊 تعداد کاربران: {result}')
    
    # نمایش مستقیم
    result = db.session.execute(text('SELECT * FROM users')).fetchall()
    for row in result:
        print(row)