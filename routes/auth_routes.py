from flask import Blueprint, request, jsonify
from database.db import get_db
import bcrypt
import jwt
import datetime
from functools import wraps
import os
from bson import ObjectId
from flask_mail import Mail, Message
import traceback

auth_bp = Blueprint('auth', __name__)
mail = Mail()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            # Check if token has Bearer prefix
            if not token.startswith('Bearer '):
                return jsonify({'message': 'Invalid token format. Token must start with "Bearer "'}), 401
            
            # Remove Bearer prefix
            token = token.split('Bearer ')[1].strip()
            
            # Decode token
            data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
            
            # Get user from database
            current_user = get_db().users.find_one({'_id': ObjectId(data['user_id'])})
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
                
            return f(current_user, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired. Please login again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token. Please login again.'}), 401
        except Exception as e:
            print(f"Token verification error: {str(e)}")
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
            
    return decorated

def get_debug_user_info(email):
    user = get_db().users.find_one({'email': email.lower()})
    if user:
        return {
            'email': user['email'],
            'user_type': user.get('user_type'),
            'created_at': user.get('created_at')
        }
    return None

@auth_bp.route('/debug/check-user/<email>', methods=['GET'])
def debug_check_user(email):
    try:
        user_info = get_debug_user_info(email)
        if user_info:
            return jsonify({
                'message': 'User found',
                'user_info': user_info
            })
        return jsonify({'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

@auth_bp.route('/client/signup', methods=['POST'])
def client_signup():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password') or not data.get('user_type'):
            return jsonify({'message': 'Missing required fields'}), 400
        
        existing_user = get_db().users.find_one({'email': data['email'].lower()})
        if existing_user:
            return jsonify({'message': 'Email already exists'}), 400
        
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
        
        user = {
            'email': data['email'].lower(),
            'password': hashed_password,
            'user_type': data['user_type'],
            'created_at': datetime.datetime.utcnow()
        }
        
        result = get_db().users.insert_one(user)
        
        token = jwt.encode({
            'user_id': str(result.inserted_id),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, os.getenv('JWT_SECRET_KEY'))
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user_type': data['user_type']
        }), 201
        
    except Exception as e:
        print(f"Error in signup: {str(e)}")
        return jsonify({'message': 'An error occurred during signup'}), 500

@auth_bp.route('/client/login', methods=['POST'])
def client_login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password') or not data.get('user_type'):
            return jsonify({'message': 'Missing email or password'}), 400
        
        user = get_db().users.find_one({
            'email': data['email'].lower(),
            'user_type': data['user_type']
        })
        
        if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, os.getenv('JWT_SECRET_KEY'))
        
        return jsonify({
            'token': token,
            'user_type': user['user_type'],
            'email': user['email']
        })
        
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({'message': 'An error occurred during login'}), 500

@auth_bp.route('/ops/signup', methods=['POST'])
def ops_signup():
    return client_signup()

@auth_bp.route('/ops/login', methods=['POST'])
def ops_login():
    return client_login()

@auth_bp.route('/user', methods=['GET'])
@token_required
def get_user(current_user):
    try:
        user_data = {
            'email': current_user['email'],
            'user_type': current_user['user_type'],
            'created_at': current_user.get('created_at')
        }
        return jsonify(user_data)
    except Exception as e:
        return jsonify({'message': 'Error fetching user data'}), 500

@auth_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    try:
        data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
        user = get_db().users.find_one({'email': data['email']})
        
        if not user:
            return jsonify({'message': 'Invalid verification link'}), 400
        
        get_db().users.update_one(
            {'email': data['email']},
            {'$set': {'verified': True}}
        )
        
        return jsonify({'message': 'Email verified successfully'})
    except:
        return jsonify({'message': 'Invalid or expired verification link'}), 400 