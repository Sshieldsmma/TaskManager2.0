import os
from flask import Flask, request, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from datetime import timedelta
import pymysql
pymysql.install_as_MySQLdb()

app = Flask(__name__)
secret_key = "mysecretkey"
app.config['SECRET_KEY'] = secret_key

DB_HOST= "mydb.cx66k868ooyp.us-east-2.rds.amazonaws.com"
DB_NAME = "mydb"
DB_USER = "rduser"
DB_PASS = "Database1006"

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_USER}@{DB_HOST}/{DB_NAME}' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    due_date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
   
@app.route('/')
def index():
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        else:
            flash('Invalid credentials, try again or register now')
            return redirect('/login')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect('/register')
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully')
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
@login_required 
def logout():
    logout_user()
    session.clear()
    return redirect('/login')



@app.route('/add', methods=['POST'])
@login_required
def add():
    title = request.form.get('title')
    due_date = request.form.get('due_date')
    if due_date:
        due_date = datetime.datetime.strptime(due_date, '%Y-%m-%d').date()
        if due_date < datetime.datetime.now().date():
            flash('Due date cannot be in the past')
            return redirect('/')
    else:
        flash('Invalid due date')
        return redirect('/')
    time = request.form.get('time')
    time = datetime.datetime.strptime(time, '%H:%M').time()
    new_task = Task(title=title, due_date=due_date, time=time)
    if not title or not due_date or not time:
        flash('Invalid task, enter all credentials')
        return redirect('/')
    db.session.add(new_task)
    flash('Task added successfully')
    db.session.commit()   
    return redirect('/')
    
    

@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    flash('Task deleted successfully')
    db.session.commit()
    return redirect('/')

@app.route('/complete/<int:task_id>')
@login_required
def complete(task_id):
    task = Task.query.get(task_id)
    task.completed = True
    db.session.commit()
    return redirect('/')

@app.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit(task_id):
    task = Task.query.get(task_id)
    task.title = request.form.get('title')
    db.session.commit()
    flash('Task edited successfully')
    return redirect('/')

@app.route('/filter/<string:filter>')
@login_required
def filter_tasks(filter):
    if filter == 'completed':
        tasks = Task.query.filter_by(completed=True).all()
    elif filter == 'non':
        tasks = Task.query.filter_by(completed=False).all()
    else:
        tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)