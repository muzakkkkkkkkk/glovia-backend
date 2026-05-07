import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)  # This allows your frontend to talk to the backend!

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    caption = db.Column(db.Text)
    username = db.Column(db.String(50)) # For easier feed loading

# --- ROUTES ---

@app.route('/')
def home():
    return "Glovia Backend is Awake! 💕"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], password_hash=hashed_pw)
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created! ✨"}), 201
    except:
        return jsonify({"error": "User already exists"}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({"message": "Welcome back! 💕", "username": user.username}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/feed', methods=['GET'])
def get_feed():
    posts = Post.query.order_by(Post.id.desc()).all()
    output = []
    for post in posts:
        output.append({
            "image_url": post.image_url,
            "caption": post.caption,
            "username": post.username or "Glovia Girl"
        })
    return jsonify(output)

@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_post = Post(
        user_id=user.id,
        image_url=data['image_url'],
        caption=data['caption'],
        username=user.username
    )
    db.session.add(new_post)
    db.session.commit()
    return jsonify({"message": "Post shared! 🌸"}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
