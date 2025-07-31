from flask import Flask, request, redirect, render_template, session, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user
from flask_babel import Babel, _
from datetime import datetime, timezone
from flask_migrate import Migrate
from flask_mail import Message
from extensions import db, babel, mail  # ✅ also import mail
from models import User, Job, Application
from urllib.parse import urlparse, urljoin
from flask_mail import Message  # Make sure this import is at the top

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_DEFAULT_TIMEZONE'] = 'UTC'
app.config['LANGUAGES'] = {'en': 'English', 'fr': 'Français'}
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'

# ✅ Mail Configuration (Use environment variables in production)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465  # ✅ Use SSL port
app.config['MAIL_USE_SSL'] = True  # ✅ Enable SSL
app.config['MAIL_USE_TLS'] = False  # ❌ Disable TLS when using SSL
app.config['MAIL_USERNAME'] = 'vybezkhid7@gmail.com'
app.config['MAIL_PASSWORD'] = 'txbr npvl fxkh uuew'  # App-specific password
app.config['MAIL_DEFAULT_SENDER'] = 'vybezkhid7@gmail.com'

# Init extensions
db.init_app(app)
migrate = Migrate(app, db)
mail.init_app(app)  # ✅ Initialize Flask-Mail
babel = Babel(app, 
    locale_selector=lambda: session.get('language', request.accept_languages.best_match(app.config['LANGUAGES'].keys())),
    timezone_selector=lambda: app.config['BABEL_DEFAULT_TIMEZONE'])

# Language selector for templates
app.jinja_env.globals['get_locale'] = lambda: session.get('language', request.accept_languages.best_match(app.config['LANGUAGES'].keys()))

@app.context_processor
def inject_languages():
    return dict(LANGUAGES=app.config['LANGUAGES'])

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    if lang_code in app.config['LANGUAGES']:
        session['language'] = lang_code
    return redirect(request.referrer or url_for('home'))

# ------------------ Models ------------------


    

# ------------------ Routes ------------------

@app.route('/')
def home():
    search_query = request.args.get('search')
    selected_category = request.args.get('category')
    categories = ['Services', 'Jobs', 'Housing', 'Gigs', 'For Sale', 'Community']

    query = Job.query.order_by(Job.id.desc())

    if search_query:
        query = query.filter(
            Job.title.ilike(f'%{search_query}%') | Job.company.ilike(f'%{search_query}%')
        )

    if selected_category:
        query = query.filter(Job.category == selected_category)

    jobs = query.all()

    user = db.session.get(User, session['user_id']) if 'user_id' in session else None


    return render_template(
    'index.html',
    jobs=jobs,
    categories=categories,
    selected_category=selected_category,
    user=user
)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("FORM DATA:", request.form)
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            flash('User already exists with that username or email.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, username=username, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')  # ✅ fixed typo


from urllib.parse import urlparse, urljoin

# Safe URL redirect checker
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_page = request.args.get('next')

    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        next_page = request.form.get('next') or ''  # Get next from hidden form input

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(_('Login successful!'), 'success')

            if next_page and next_page != 'None' and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('home'))

        flash(_('Invalid username/email or password.'), 'danger')
        return redirect(url_for('login', next=next_page))

    return render_template('login.html', next=next_page)





@app.route('/logout')
def logout():
    session.clear()
    flash(_('Logged out.'), 'info')
    return redirect(url_for('home'))

@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form['salary']
        category = request.form['category']
        description = request.form['description']
        latitude = request.form.get('latitude') or None
        longitude = request.form.get('longitude') or None
        posted_time = datetime.now(timezone.utc)

        job = Job(
            title=title,
            company=company,
            location=location,
            salary=float(salary),
            currency="USD",
            category=category,
            description=description,
            latitude=latitude,
            longitude=longitude,
            user_id=session['user_id'],
            posted_time=posted_time
        )

        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for('home'))

    return render_template('post_job.html', title=_('Post a Job'))


@app.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
def edit_job(job_id):
    if 'user_id' not in session:
        flash('Login required.', 'danger')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        job.title = request.form['title']
        job.company = request.form['company']
        job.location = request.form['location']
        job.salary = float(request.form['salary'])
        job.category = request.form['category']
        job.description = request.form['description']
        db.session.commit()
        flash('Job updated successfully.', 'success')
        return redirect(url_for('home'))

    return render_template('edit_job.html', job=job)

@app.route('/delete-job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    if 'user_id' not in session:
        flash('Login required.', 'danger')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)

    # Optional but recommended: Ensure the logged-in user owns the job
    if job.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('home'))

    db.session.delete(job)
    db.session.commit()
    flash('Job deleted successfully.', 'success')
    return redirect(url_for('home'))


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    user = db.session.get(User, session['user_id']) if 'user_id' in session else None
    return render_template('job_detail.html', job=job, user=user)



@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Save application to DB
        application = Application(
            job_id=job.id,
            name=name,
            email=email,
            message=message
        )
        db.session.add(application)
        db.session.commit()

        # ✅ SEND EMAIL TO JOB POSTER
        msg = Message(
            subject=f"New Application for {job.title}",
            recipients=[job.poster.email],
            reply_to=email
        )

        msg.body = f"""
Hello {job.poster.full_name or job.poster.username},

You've received a new application for your job post: {job.title}

From: {name}
Email: {email}

Message:
{message}

-- Job Portal
"""

        msg.html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>📩 New Application Received</h2>
            <p><strong>Job Title:</strong> {job.title}</p>
            <p><strong>From:</strong> {name} (<a href="mailto:{email}">{email}</a>)</p>
            <p><strong>Message:</strong></p>
            <blockquote style="border-left: 4px solid #0066cc; margin: 10px 0; padding-left: 10px;">
              {message}
            </blockquote>
            <hr>
            <p style="font-size: 13px; color: #777;">Sent via Job Portal | Do not reply to this email directly.</p>
          </body>
        </html>
        """

        try:
            mail.send(msg)
        except Exception as e:
            print("❌ Email send failed:", e)
            flash(_('Application submitted, but email failed to send.'), 'warning')
        else:
            flash(_('Application submitted successfully!'), 'success')

        return redirect(url_for('job_detail', job_id=job.id))

    return render_template('apply.html', job=job)





# Show profile
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Login required to view profile.', 'warning')
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    jobs = Job.query.filter_by(user_id=user.id).all()  # if you're showing jobs
    return render_template('profile.html', user=user, jobs=jobs)





# Handle update form
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('You must be logged in to update your profile.', 'danger')
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    if user:
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.location = request.form.get('location')  # ✅ MUST BE HERE
        user.bio = request.form.get('bio')            # ✅ MUST BE HERE

        db.session.commit()
        flash('Profile updated successfully.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('profile'))









@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            flash('If this email exists, a reset link will be sent.', 'info')
        else:
            flash('No user found with that email.', 'danger')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

@app.route('/toggle_dark_mode', methods=['POST'])
@login_required
def toggle_dark_mode():
    data = request.get_json()
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/confirm_logout', methods=['GET', 'POST'])
def confirm_logout():
    if 'user_id' not in session:
        flash(_('You must be logged in.'), 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form['password']
        user = db.session.get(User, session['user_id'])

        if user and check_password_hash(user.password, password):
            session.clear()
            flash(_('Logged out successfully.'), 'info')
            return redirect(url_for('home'))
        else:
            flash(_('Incorrect password.'), 'danger')

    return render_template('confirm_logout.html')




# ------------------ Run ------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
