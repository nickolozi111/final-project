from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    movies = db.relationship('Movie', backref='owner', lazy=True)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            session['user'] = u
            flash('Login successful!', 'success')
            return redirect(url_for('movie_list'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        existing_user = User.query.filter_by(username=u).first()
        if existing_user:
            flash('User already exists', 'warning')
            return render_template('register.html')
        hashed_pw = generate_password_hash(p)
        new_user = User(username=u, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/movies')
def movie_list():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['user']).first()
    movies = Movie.query.filter_by(user_id=user.id).all()
    return render_template('movies.html', movies=movies)

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        user = User.query.filter_by(username=session['user']).first()
        new_movie = Movie(title=title, description=desc, user_id=user.id)
        db.session.add(new_movie)
        db.session.commit()
        flash('Movie added!', 'success')
        return redirect(url_for('movie_list'))
    return render_template('add_movie.html')

@app.route('/delete_movie/<int:movie_id>')
def delete_movie(movie_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    movie = Movie.query.get_or_404(movie_id)
    user = User.query.filter_by(username=session['user']).first()
    if movie.user_id != user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('movie_list'))
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted.', 'info')
    return redirect(url_for('movie_list'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
