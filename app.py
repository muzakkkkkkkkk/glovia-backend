import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app) # Vital for frontend-backend communication

# Database Configuration for Neon
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
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
    username = db.Column(db.String(50))
    likes = db.Column(db.Integer, default=0)

class Message(db.Model): # For one-on-one messaging
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    receiver = db.Column(db.String(50))
    text = db.Column(db.Text)

# --- ROUTES ---

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({"message": "Welcome back! 💕", "username": user.username}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/search', methods=['GET']) # To find unique usernames
def search_user():
    username = request.args.get('username')
    users = User.query.filter(User.username.ilike(f'%{username}%')).all()
    return jsonify([{"username": u.username} for u in users])

@app.route('/like/<int:post_id>', methods=['POST']) # For liking posts
def like_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post.likes += 1
        db.session.commit()
        return jsonify({"likes": post.likes}), 200
    return jsonify({"error": "Post not found"}), 404

@app.route('/send_message', methods=['POST']) # Personal messaging
def send_msg():
    data = request.get_json()
    new_msg = Message(sender=data['sender'], receiver=data['receiver'], text=data['text'])
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({"message": "Sent! 💌"}), 201

# Place all new routes ABOVE this line
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
