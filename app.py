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

# --- DATABASE MODELS ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    text = db.Column(db.Text)
    group_id = db.Column(db.Integer, default=0) # 0 = Global "All Girls Chat"
    recipient = db.Column(db.String(50), nullable=True) # For 1-on-1
    is_personal = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower = db.Column(db.String(50))
    followed = db.Column(db.String(50))

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

@app.route('/feed', methods=['GET'])
def get_feed():
    posts = Post.query.order_by(Post.id.desc()).all()
    return jsonify([{
        "id": p.id, 
        "image_url": p.image_url, 
        "caption": p.caption, 
        "username": p.username, 
        "likes": p.likes,                 # Added Likes
        "comment_count": p.comment_count   # Added Comments
    } for p in posts])

@app.route('/messages/<int:group_id>', methods=['GET'])
def get_messages(group_id):
    # Fetch messages for specific group or Global (0)
    msgs = Message.query.filter_by(group_id=group_id).order_by(Message.id.asc()).all()
    return jsonify([{
        "id": m.id,
        "sender": m.sender,
        "text": m.text,
        "seen_by": m.seen_by.split(',') if m.seen_by else []
    } for m in msgs])

@app.route('/mark_seen', methods=['POST'])
def mark_seen():
    data = request.get_json()
    msg = Message.query.get(data['message_id'])
    current_seen = msg.seen_by.split(',') if msg.seen_by else []
    if data['username'] not in current_seen:
        current_seen.append(data['username'])
        msg.seen_by = ",".join(current_seen)
        db.session.commit()
    return jsonify({"status": "seen"}), 200

# --- NEW ROUTES ---
@app.route('/search_user', methods=['GET'])
def search():
    query = request.args.get('username')
    user = User.query.filter_by(username=query).first()
    if user:
        is_following = Follow.query.filter_by(follower=request.args.get('viewer'), followed=query).first() is not None
        return jsonify({"username": user.username, "is_following": is_following}), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/follow', methods=['POST'])
def follow_user():
    data = request.get_json()
    new_follow = Follow(follower=data['follower'], followed=data['followed'])
    db.session.add(new_follow)
    db.session.commit()
    return jsonify({"message": "Following"}), 200

# Place all new routes ABOVE this line
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
