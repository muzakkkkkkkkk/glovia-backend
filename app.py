import bcrypt
from flask import request, jsonify
# Add this to your imports
import bcrypt

# Add this class below your Message class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.String(255), default="Welcome to Glovia! ✨")
    profile_pic = db.Column(db.String(255), default="https://placehold.co/100x100?text=Glovia")
    
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
