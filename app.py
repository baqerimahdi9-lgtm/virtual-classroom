"""
فایل اصلی پروژه - سامانه کلاس مجازی
"""
# ==================== Monkey Patch (باید اول باشه!) ====================
import eventlet
eventlet.monkey_patch()

# ==================== Importها ====================
from flask import Flask, render_template, request, redirect
from flask import url_for, flash, send_from_directory, session
from flask_login import LoginManager, login_user, login_required
from flask_login import logout_user, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from PIL import Image, ImageDraw
from datetime import datetime
import random
import os
import io
import string
import time
import traceback
import logging

from config import Config
from models import db, User, Classroom, FileUpload, Message, Ticket

# ==================== لاگ‌گیری ====================
logging.basicConfig(level=logging.INFO)


# ==================== راه‌اندازی ====================
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'برای دسترسی باید وارد شوید'
login_manager.login_message_category = 'warning'


# ==================== ساخت جداول و کاربران پیش‌فرض ====================
with app.app_context():
    try:
        db.create_all()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        print('✅ دیتابیس آماده شد')

        # ساخت کاربران پیش‌فرض
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@site.com',
                password=generate_password_hash('admin123'),
                role='admin',
                full_name='مدیر سیستم'
            )
            db.session.add(admin)
            print('✅ ادمین ساخته شد')

        if not User.query.filter_by(username='teacher').first():
            teacher = User(
                username='teacher',
                email='teacher@site.com',
                password=generate_password_hash('teacher123'),
                role='teacher',
                full_name='استاد نمونه'
            )
            db.session.add(teacher)
            print('✅ استاد ساخته شد')

        if not User.query.filter_by(username='student').first():
            student = User(
                username='student',
                email='student@site.com',
                password=generate_password_hash('student123'),
                role='student',
                full_name='دانشجوی نمونه'
            )
            db.session.add(student)
            print('✅ دانشجو ساخته شد')

        db.session.commit()
        print('✅ همه کاربران آماده هستند')
    except Exception as e:
        print(f'❌ خطا در راه‌اندازی: {e}')
        traceback.print_exc()


# ==================== لود کاربر ====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== تزئین‌گرها ====================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('دسترسی فقط برای مدیر سیستم', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapper


def teacher_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['teacher', 'admin']:
            flash('دسترسی فقط برای استاد', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapper


# ==================== کد امنیتی ====================
def generate_captcha_image():
    chars = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(chars, k=5))

    img = Image.new('RGB', (160, 55), color=(245, 248, 255))
    draw = ImageDraw.Draw(img)

    for i, ch in enumerate(code):
        x = 15 + i * 28
        y = random.randint(8, 18)
        r = random.randint(0, 100)
        g = random.randint(50, 120)
        b = random.randint(150, 255)
        draw.text((x, y), ch, fill=(r, g, b))

    for _ in range(6):
        x1 = random.randint(0, 160)
        y1 = random.randint(0, 55)
        x2 = random.randint(0, 160)
        y2 = random.randint(0, 55)
        draw.line([(x1, y1), (x2, y2)], fill=(150, 150, 200), width=1)

    for _ in range(80):
        x = random.randint(0, 160)
        y = random.randint(0, 55)
        draw.point((x, y), fill=(100, 100, 180))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return code, buf


@app.route('/captcha')
def captcha():
    code, img = generate_captcha_image()
    session['captcha'] = code
    return img.getvalue(), 200, {'Content-Type': 'image/png'}


# ==================== صفحه اصلی ====================
@app.route('/')
def index():
    try:
        classes = Classroom.query.filter_by(is_active=True)\
                                 .order_by(Classroom.created_at.desc()).limit(6).all()
        stats = {
            'classes': Classroom.query.count(),
            'users': User.query.count(),
            'teachers': User.query.filter_by(role='teacher').count(),
        }
        return render_template('index.html', classes=classes, stats=stats)
    except Exception as e:
        error_details = traceback.format_exc()
        print(f'❌ خطای index: {e}')
        print(error_details)
        return f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: monospace; padding: 20px; background: #fee; direction: ltr;">
            <h1 style="color: red;">Server Error</h1>
            <h2>Error Type:</h2>
            <pre style="background: #fff; padding: 10px; border: 1px solid #ccc;">{type(e).__name__}: {str(e)}</pre>
            <h2>Full Traceback:</h2>
            <pre style="background: #fff; padding: 10px; border: 1px solid #ccc; overflow: auto;">{error_details}</pre>
        </body>
        </html>
        """, 500


# ==================== ثبت‌نام ====================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        captcha_input = request.form.get('captcha', '').upper()

        if captcha_input != session.get('captcha', ''):
            flash('کد امنیتی اشتباه است', 'danger')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('نام کاربری حداقل ۳ کاراکتر', 'danger')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('رمز عبور حداقل ۶ کاراکتر', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('نام کاربری موجود است', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('ایمیل موجود است', 'danger')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            full_name=full_name or username,
            role='student'
        )
        db.session.add(user)
        db.session.commit()

        flash('ثبت‌نام موفق! حالا وارد شوید', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# ==================== ورود ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        captcha_input = request.form.get('captcha', '').upper()

        if captcha_input != session.get('captcha', ''):
            flash('کد امنیتی اشتباه است', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('خوش آمدی ' + user.username + '!', 'success')
            if user.role == 'admin':
                return redirect(url_for('admin_tickets'))
            return redirect(url_for('dashboard'))

        flash('نام کاربری یا رمز اشتباه است', 'danger')

    return render_template('login.html')


# ==================== خروج ====================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('با موفقیت خارج شدید', 'success')
    return redirect(url_for('index'))


# ==================== داشبورد ====================
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        classes = Classroom.query.filter_by(teacher_id=current_user.id)\
                                 .order_by(Classroom.created_at.desc()).all()
    else:
        classes = Classroom.query.filter_by(is_active=True)\
                                 .order_by(Classroom.created_at.desc()).all()

    stats = {
        'total_classes': Classroom.query.count(),
        'my_classes': len(classes),
        'total_students': User.query.filter_by(role='student').count(),
        'total_messages': Message.query.count(),
    }
    return render_template('dashboard.html', classes=classes, stats=stats)


# ==================== جستجو ====================
@app.route('/search')
@login_required
def search():
    from sqlalchemy import or_
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    query = Classroom.query.filter_by(is_active=True)

    if q:
        query = query.filter(
            or_(
                Classroom.title.ilike(f'%{q}%'),
                Classroom.description.ilike(f'%{q}%')
            )
        )

    results = query.order_by(Classroom.created_at.desc()).all()

    return render_template('search.html', results=results, q=q, category=category, categories=[])


# ==================== ساخت کلاس ====================
@app.route('/class/create', methods=['GET', 'POST'])
@login_required
@teacher_required
def create_class():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        meeting_url = request.form.get('meeting_url', '').strip()
        start_time = request.form.get('start_time', '')
        video_url = request.form.get('video_url', '').strip()
        video_type = request.form.get('video_type', 'aparat')

        if not title or not meeting_url:
            flash('عنوان و لینک لایو الزامی است', 'danger')
            return redirect(url_for('create_class'))

        classroom = Classroom(
            title=title,
            description=description,
            category=category,
            meeting_url=meeting_url,
            video_url=video_url,
            video_type=video_type,
            teacher_id=current_user.id,
            start_time=datetime.strptime(start_time, '%Y-%m-%dT%H:%M') if start_time else datetime.utcnow()
        )
        db.session.add(classroom)
        db.session.commit()

        flash('کلاس ساخته شد', 'success')
        return redirect(url_for('dashboard'))

    return render_template('create_class.html')


# ==================== ویرایش کلاس ====================
@app.route('/class/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_class(class_id):
    classroom_obj = Classroom.query.get_or_404(class_id)

    if classroom_obj.teacher_id != current_user.id and current_user.role != 'admin':
        flash('دسترسی ندارید', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        classroom_obj.title = request.form.get('title', '').strip()
        classroom_obj.description = request.form.get('description', '').strip()
        classroom_obj.category = request.form.get('category', '').strip()
        classroom_obj.meeting_url = request.form.get('meeting_url', '').strip()
        classroom_obj.video_url = request.form.get('video_url', '').strip()
        classroom_obj.video_type = request.form.get('video_type', 'aparat')

        db.session.commit()
        flash('کلاس ویرایش شد', 'success')
        return redirect(url_for('classroom', class_id=class_id))

    return render_template('edit_class.html', classroom=classroom_obj)


# ==================== حذف کلاس ====================
@app.route('/class/<int:class_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_class(class_id):
    classroom_obj = Classroom.query.get_or_404(class_id)

    if classroom_obj.teacher_id != current_user.id and current_user.role != 'admin':
        flash('دسترسی ندارید', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(classroom_obj)
    db.session.commit()
    flash('کلاس حذف شد', 'success')
    return redirect(url_for('dashboard'))


# ==================== مشاهده کلاس ====================
@app.route('/class/<int:class_id>')
@login_required
def classroom(class_id):
    classroom_obj = Classroom.query.get_or_404(class_id)

    classroom_obj.views = (classroom_obj.views or 0) + 1
    db.session.commit()

    files = FileUpload.query.filter_by(classroom_id=class_id, file_type='file').all()
    videos = FileUpload.query.filter_by(classroom_id=class_id, file_type='video').all()

    return render_template('classroom.html',
                           classroom=classroom_obj,
                           files=files,
                           videos=videos)


# ==================== لایو ====================
@app.route('/class/<int:class_id>/live')
@login_required
def live(class_id):
    classroom_obj = Classroom.query.get_or_404(class_id)
    return render_template('live.html', classroom=classroom_obj)


# ==================== آپلود فایل ====================
def allowed_file(filename, allowed_set):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_set


@app.route('/class/<int:class_id>/upload', methods=['POST'])
@login_required
@teacher_required
def upload_file(class_id):
    file = request.files.get('file')

    if not file or file.filename == '':
        flash('فایلی انتخاب نشده', 'danger')
        return redirect(url_for('classroom', class_id=class_id))

    ext = file.filename.rsplit('.', 1)[1].lower()

    if ext in app.config['ALLOWED_VIDEO_EXTENSIONS']:
        file_type = 'video'
        folder = app.config['VIDEO_FOLDER']
    elif ext in app.config['ALLOWED_FILE_EXTENSIONS']:
        file_type = 'file'
        folder = app.config['FILE_FOLDER']
    else:
        flash('فرمت فایل مجاز نیست', 'danger')
        return redirect(url_for('classroom', class_id=class_id))

    original_name = file.filename
    filename = secure_filename(file.filename)
    filename = str(int(time.time())) + '_' + filename
    filepath = os.path.join(folder, filename)
    file.save(filepath)

    file_size = os.path.getsize(filepath)

    fu = FileUpload(
        filename=filename,
        original_name=original_name,
        file_type=file_type,
        file_size=file_size,
        uploaded_by=current_user.id,
        classroom_id=class_id
    )
    db.session.add(fu)
    db.session.commit()

    flash('فایل با موفقیت آپلود شد', 'success')
    return redirect(url_for('classroom', class_id=class_id))


# ==================== دانلود فایل ====================
@app.route('/download/<int:file_id>')
@login_required
def download(file_id):
    fu = FileUpload.query.get_or_404(file_id)

    if fu.file_type == 'video':
        folder = app.config['VIDEO_FOLDER']
    else:
        folder = app.config['FILE_FOLDER']

    return send_from_directory(
        folder,
        fu.filename,
        as_attachment=True,
        download_name=fu.original_name
    )


# ==================== حذف فایل ====================
@app.route('/file/<int:file_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_file(file_id):
    fu = FileUpload.query.get_or_404(file_id)

    if fu.uploader.id != current_user.id and current_user.role != 'admin':
        flash('دسترسی ندارید', 'danger')
        return redirect(url_for('dashboard'))

    if fu.file_type == 'video':
        folder = app.config['VIDEO_FOLDER']
    else:
        folder = app.config['FILE_FOLDER']

    filepath = os.path.join(folder, fu.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    classroom_id = fu.classroom_id
    db.session.delete(fu)
    db.session.commit()

    flash('فایل حذف شد', 'success')
    return redirect(url_for('classroom', class_id=classroom_id))


# ==================== پروفایل ====================
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', '').strip()
        current_user.bio = request.form.get('bio', '').strip()
        current_user.email = request.form.get('email', '').strip()

        db.session.commit()
        flash('پروفایل به‌روزرسانی شد', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html')


# ==================== پشتیبانی ====================
@app.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        priority = request.form.get('priority', 'normal')

        if not subject or not message:
            flash('موضوع و پیام الزامی است', 'danger')
            return redirect(url_for('support'))

        ticket = Ticket(
            subject=subject,
            message=message,
            priority=priority,
            user_id=current_user.id
        )
        db.session.add(ticket)
        db.session.commit()
        flash('تیکت ارسال شد', 'success')
        return redirect(url_for('support'))

    tickets = Ticket.query.filter_by(user_id=current_user.id)\
                          .order_by(Ticket.created_at.desc()).all()
    return render_template('support.html', tickets=tickets)


# ==================== ادمین ====================
@app.route('/admin/tickets')
@login_required
@admin_required
def admin_tickets():
    filter_status = request.args.get('status', '')
    query = Ticket.query
    if filter_status:
        query = query.filter_by(status=filter_status)
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin_tickets.html', tickets=tickets, filter_status=filter_status)


@app.route('/admin/ticket/<int:ticket_id>/reply', methods=['POST'])
@login_required
@admin_required
def reply_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    reply = request.form.get('reply', '').strip()

    if reply:
        ticket.reply = reply
        ticket.status = 'answered'
        db.session.commit()
        flash('پاسخ ارسال شد', 'success')

    return redirect(url_for('admin_tickets'))


# ==================== Socket.IO ====================
@socketio.on('join')
def on_join(data):
    room = str(data['room'])
    join_room(room)
    emit('status', {
        'msg': current_user.username + ' وارد کلاس شد',
        'type': 'join'
    }, room=room)


@socketio.on('leave')
def on_leave(data):
    room = str(data['room'])
    leave_room(room)
    emit('status', {
        'msg': current_user.username + ' خارج شد',
        'type': 'leave'
    }, room=room)


@socketio.on('message')
def handle_message(data):
    room = str(data['room'])
    msg_content = data['msg'].strip()

    if not msg_content:
        return

    msg = Message(
        content=msg_content,
        user_id=current_user.id,
        classroom_id=int(room)
    )
    db.session.add(msg)
    db.session.commit()

    emit('message', {
        'user': current_user.username,
        'msg': msg_content,
        'time': datetime.now().strftime('%H:%M'),
        'user_id': current_user.id
    }, room=room)


# ==================== اجرا ====================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f'🚀 Server running on port {port}')
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True
    )