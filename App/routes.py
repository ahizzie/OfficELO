from flask import request, jsonify, abort
from app.models import User, Match
from werkzeug.security import generate_password_hash, check_password_hash
import jwt  # For JSON Web Tokens

# Replace with your secret key for production
SECRET_KEY = 'your_secret_key'

def create_token(user_id):
  payload = {'user_id': user_id}
  return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def decode_token(token):
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    return payload['user_id']
  except jwt.exceptions.DecodeError:
    abort(401, 'Invalid token')

# User registration route
@app.route('/register', methods=['POST'])
def register():
  data = request.get_json()
  username = data.get('username')
  email = data.get('email')
  password = data.get('password')

  if not all([username, email, password]):
    return jsonify({'error': 'Missing required fields'}), 400

  existing_user = User.query.filter_by(email=email).first()
  if existing_user:
    return jsonify({'error': 'Email already exists'}), 400

  hashed_password = generate_password_hash(password)
  user = User(username=username, email=email, password=hashed_password)
  db.session.add(user)
  db.session.commit()

  return jsonify({'message': 'User created successfully', 'token': create_token(user.id)}), 201

# User login route
@app.route('/login', methods=['POST'])
def login():
  data = request.get_json()
  email = data.get('email')