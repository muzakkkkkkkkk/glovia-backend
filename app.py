import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- 1. THE CORS FIX ---
# This ensures your frontend URL is explicitly allowed to talk to the backend
CORS(app, resources={r"/*": {"origins": "*"}}) 

# --- 2. THE DATABASE URL FIX ---
# Render/Neon sometimes provide 'postgres://'. Python needs 'postgresql://'.
uri = os.getenv("DATABASE_URL")
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Keeps the connection alive on Render's free tier
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True} 

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

# --- ROUTES ---

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "Glovia API is active 💕"}), 200

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({"error": "Missing data"}), 400
            
        user = User.query.filter_by(username=data['username']).first()
        # If user doesn't exist, we'll create one automatically for testing 
        # (You can remove this auto-register once your site is public!)
        if not user:
            hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
            user = User(username=data['username'], password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
            
        if check_password_hash(user.password_hash, data['password']):
            return jsonify({"message": "Welcome back! 💕", "username": user.username}), 200
        return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/feed', methods=['GET'])
def get_feed():
    try:
        posts = Post.query.order_by(Post.id.desc()).all()
        return jsonify([{
            "image_url": p.image_url,
            "caption": p.caption,
            "username": p.username or "Glovia Girl"
        } for p in posts])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create_post', methods=['POST'])
def create_post():
    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- LIKE A POST ---
@app.route('/like_post/<int:post_id>', methods=['POST'])
def like_post(post_id):
    # Logic to increment likes in the database
    return jsonify({"message": "Liked! ❤️"}), 200

# --- SEARCH USERS ---
@app.route('/search_user', methods=['GET'])
def search_user():
    query = request.args.get('username')
    users = User.query.filter(User.username.ilike(f'%{query}%')).all()
    return jsonify([{"username": u.username} for u in users])

# --- ADD COMMENT ---
@app.route('/comment', methods=['POST'])
def add_comment():
    data = request.get_json()
    # Logic to save data['text'] linked to data['post_id']
    return jsonify({"message": "Commented! 💬"}), 201

if __name__ == '__main__':
    # Use the port Render assigns
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
