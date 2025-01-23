from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gallery.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['SECRET_KEY'] = 'mysecretkey'  # Necesario para la sesión
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Definir el modelo de usuario
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Definir el modelo de pintura
class Painting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)

# Cargar el usuario por su ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    paintings = Painting.query.all()
    return render_template('index.html', paintings=paintings)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Verificar la contraseña
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.username != 'admin':  # Solo el admin puede acceder al dashboard
        return redirect(url_for('index'))

    # Mostrar las pinturas en el dashboard
    paintings = Painting.query.all()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            new_painting = Painting(name=name, description=description, image_filename=filename)
            db.session.add(new_painting)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))

    return render_template('dashboard.html', paintings=paintings)

@app.route('/delete_painting/<int:painting_id>', methods=['POST'])
@login_required
def delete_painting(painting_id):
    if current_user.username != 'admin':
        return redirect(url_for('index'))

    painting = Painting.query.get(painting_id)
    if painting:
        db.session.delete(painting)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_painting/<int:painting_id>', methods=['GET', 'POST'])
@login_required
def update_painting(painting_id):
    if current_user.username != 'admin':
        return redirect(url_for('index'))

    painting = Painting.query.get(painting_id)

    if request.method == 'POST':
        painting.name = request.form['name']
        painting.description = request.form['description']
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            painting.image_filename = filename
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('update_painting.html', painting=painting)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crear base de datos si no existe
        # Crear un usuario admin si no existe
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123')  # Asegúrate de cambiar la contraseña en producción
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
