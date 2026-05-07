import bcrypt
from flask import request, jsonify
# Add this to your imports
import bcrypt

# Add this class below your Message class
class User(db.Model):
    __tablename__ = 'user' # Must be lowercase 'user' to match Neon
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(255), default="Welcome to Glovia! ✨")
    profile_pic = db.Column(db.String(255), default="https://placehold.co/100x100?text=Glovia")

class Post(db.Model):
    __tablename__ = 'post' # Must be lowercase 'post' to match Neon
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    author = db.relationship('User', backref=db.backref('posts', lazy=True))
    
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room
from cryptography.fernet import Fernet
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://neondb_owner:npg_oNW4Jab8ABlD@ep-dry-moon-ao3p1ubh-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'glovia_pink_key_2026'

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins=["https://glovia-frontend.onrender.com", "http://localhost:3000"], async_mode='eventlet')
cipher = Fernet(Fernet.generate_key())

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(255), default="Welcome to Glovia! ✨")
    profile_pic = db.Column(db.String(255), default="https://placehold.co/100x100?text=Glovia")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(50))
    sender = db.Column(db.String(50))
    content = db.Column(db.LargeBinary)

@socketio.on('join')
def on_join(data):
    join_room(data['room'])

@socketio.on('send_msg')
def handle_msg(data):
    # This must match 'sender' from frontend
    content = data['content']
    sender = data.get('sender', 'Anonymous')
    
    new_msg = Message(room=data['room'], sender=sender, content=content.encode())
    db.session.add(new_msg)
    db.session.commit()

    emit('message', data, room=data['room'])

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    # Check if username exists
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken! ✨"}), 409

    # Scramble the password for security
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Save to database
    new_user = User(username=username, password_hash=hashed)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Account created successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and bcrypt.checkpw(data.get('password').encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({
            "message": "Login success!",
            "user": {"username": user.username, "bio": user.bio}
        }), 200
        
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/feed', methods=['GET'])
def get_feed():
    # 1. Fetch all posts from the database, newest first
    posts = Post.query.order_by(Post.created_at.desc()).all()
    
    # 2. Format the data into a list that the frontend can read
    output = []
    for post in posts:
        output.append({
            "id": post.id,
            "username": post.author.username,
            "profile_pic": post.author.profile_pic,
            "image_url": post.image_url,
            "caption": post.caption,
            "created_at": post.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    
    # 3. Send the list back to Glovia's home screen
    return jsonify(output)

@app.route('/create_post', methods=['POST'])
def create_post():
    data = request.get_json()
    username = data.get('username')
    image_url = data.get('image_url')
    caption = data.get('caption')

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Create the new post and link it to the user's ID
    new_post = Post(user_id=user.id, image_url=image_url, caption=caption)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"message": "Post shared to feed! ✨"}), 201

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
