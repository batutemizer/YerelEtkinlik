from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from models import db, User, Event, Message
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Upload klasörünü oluştur
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)
migrate = Migrate(app, db)

# Veritabanı tablolarını oluştur
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ana sayfa
@app.route('/')
def index():
    events = Event.query.filter_by(is_approved=True).order_by(Event.date.desc()).all()
    return render_template('index.html', events=events)

# Etkinlikler sayfası
@app.route('/etkinlikler')
def events():
    events = Event.query.filter_by(is_approved=True).order_by(Event.date.desc()).all()
    return render_template('etkinlikler.html', events=events)

# Etkinlik detay sayfası
@app.route('/etkinlik/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('etkinlik_detay.html', event=event)

# Etkinlik oluşturma
@app.route('/etkinlik/olustur', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
        location = request.form['location']
        max_participants = request.form['max_participants']
        
        event = Event(
            title=title,
            description=description,
            date=date,
            location=location,
            max_participants=max_participants,
            user_id=current_user.id
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                event.image = filename
        
        db.session.add(event)
        db.session.commit()
        flash('Etkinlik başarıyla oluşturuldu ve onay bekliyor.')
        return redirect(url_for('events'))
    
    return render_template('etkinlik_olustur.html')

# Etkinliğe katılma
@app.route('/join_event/<int:event_id>', methods=['POST'])
@login_required
def join_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    # Etkinlik onaylanmış mı kontrol et
    if not event.is_approved:
        flash('Bu etkinliğe henüz katılamazsınız.', 'warning')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Kullanıcı zaten katılmış mı kontrol et
    if current_user in event.participants.all():
        flash('Bu etkinliğe zaten katıldınız.', 'info')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Etkinlik dolu mu kontrol et
    if len(event.participants.all()) >= event.max_participants:
        flash('Üzgünüz, etkinlik kontenjanı dolmuştur.', 'warning')
        return redirect(url_for('event_detail', event_id=event_id))
    
    # Etkinliğe katıl
    event.participants.append(current_user)
    db.session.commit()
    
    flash('Etkinliğe başarıyla katıldınız!', 'success')
    return redirect(url_for('event_detail', event_id=event_id))

# Admin paneli ana sayfası
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
        return redirect(url_for('index'))
    
    # İstatistikler
    total_users = User.query.count()
    approved_events = Event.query.filter_by(is_approved=True).all()
    pending_events = Event.query.filter_by(is_approved=False).all()
    total_events = Event.query.count()
    
    # Kullanıcılar ve etkinlikler
    users = User.query.all()
    all_events = Event.query.all()
    
    return render_template('admin_panel.html',
                         total_users=total_users,
                         approved_events=approved_events,
                         pending_events=pending_events,
                         total_events=total_events,
                         users=users,
                         all_events=all_events)

@app.route('/admin/event/<int:event_id>/approve', methods=['POST'])
@login_required
def approve_event(event_id):
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    event.is_approved = True
    db.session.commit()
    
    flash('Etkinlik başarıyla onaylandı.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/event/<int:event_id>/reject', methods=['POST'])
@login_required
def reject_event(event_id):
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    flash('Etkinlik reddedildi ve silindi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/user/<int:user_id>/make-admin', methods=['POST'])
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    
    flash(f'{user.username} kullanıcısı admin yapıldı.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Kendinizi silemezsiniz.', 'danger')
        return redirect(url_for('admin_panel'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'{user.username} kullanıcısı silindi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    if not current_user.is_admin:
        flash('Bu işlem için yetkiniz yok.', 'danger')
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    
    flash('Etkinlik başarıyla silindi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/kayit', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        password2 = request.form['password2']
        
        if password != password2:
            flash('Şifreler eşleşmiyor.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kullanılıyor.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Bu email adresi zaten kullanılıyor.')
            return redirect(url_for('register'))
        
        if User.query.filter_by(phone=phone).first():
            flash('Bu telefon numarası zaten kullanılıyor.')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, phone=phone)
        user.set_password(password)
        verification_code = user.generate_verification_code()
        
        db.session.add(user)
        db.session.commit()
        
        # Doğrulama sayfasına yönlendir
        return render_template('dogrulama.html', verification_code=verification_code)
    
    return render_template('kayit.html')

@app.route('/verify-phone', methods=['POST'])
def verify_phone():
    code = request.form.get('verification_code')
    user = User.query.filter_by(verification_code=code).first()
    
    if user:
        user.is_verified = True
        user.verification_code = None  # Kodu temizle
        db.session.commit()
        flash('Telefon numaranız başarıyla doğrulandı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Geçersiz doğrulama kodu.', 'danger')
        return redirect(url_for('register'))

@app.route('/resend-code')
def resend_code():
    # Bu fonksiyon gerçek bir SMS gönderimi yapmaz
    # Sadece yeni bir kod oluşturur ve gösterir
    user = User.query.filter_by(is_verified=False).order_by(User.id.desc()).first()
    if user:
        verification_code = user.generate_verification_code()
        db.session.commit()
        return render_template('dogrulama.html', verification_code=verification_code)
    return redirect(url_for('register'))

@app.route('/giris', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Geçersiz kullanıcı adı veya şifre.')
    
    return render_template('giris.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.')
    return redirect(url_for('index'))

@app.route('/profil')
@login_required
def profile():
    return render_template('profil.html')

@app.route('/profil/guncelle', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    # Kullanıcı adı ve email kontrolü
    if username != current_user.username:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Bu kullanıcı adı zaten kullanılıyor.', 'danger')
            return redirect(url_for('profile'))

    if email != current_user.email:
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Bu e-posta adresi zaten kullanılıyor.', 'danger')
            return redirect(url_for('profile'))

    # Şifre değişikliği kontrolü
    if current_password and new_password:
        if not current_user.check_password(current_password):
            flash('Mevcut şifre yanlış.', 'danger')
            return redirect(url_for('profile'))
        current_user.set_password(new_password)

    # Profil bilgilerini güncelle
    current_user.username = username
    current_user.email = email
    db.session.commit()

    flash('Profil bilgileriniz başarıyla güncellendi.', 'success')
    return redirect(url_for('profile'))

@app.route('/mesaj_gonder', methods=['GET', 'POST'])
@login_required
def mesaj_gonder():
    admins = User.query.filter_by(is_admin=True).all()
    if request.method == 'POST':
        content = request.form['content']
        receiver_id = request.form['receiver_id']
        message = Message(sender_id=current_user.id, receiver_id=receiver_id, content=content)
        db.session.add(message)
        db.session.commit()
        flash('Mesajınız admin kullanıcıya gönderildi!', 'success')
        return redirect(url_for('index'))
    return render_template('mesaj_gonder.html', admins=admins)

@app.route('/admin/mesajlar')
@login_required
def admin_mesajlar():
    if not current_user.is_admin:
        abort(403)
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    return render_template('admin_mesajlar.html', messages=messages)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 