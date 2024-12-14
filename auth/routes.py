from google.oauth2 import id_token
from google.auth.transport import requests
from flask import Blueprint, request, jsonify, session
import os
from auth.models import UserModel

auth = Blueprint('auth', __name__)

@auth.route('/auth/google', methods=['POST'])
def google_auth():
    try:
        # Log the incoming request
        print("Received auth request:", request.json)
        
        # Verify Google token
        token = request.json['token']
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            os.getenv('GOOGLE_CLIENT_ID')
        )
        
        print("Verified token info:", idinfo)  # Log the token info

        # Create/update user
        user_model = UserModel()
        user_id = user_model.create_user(idinfo)
        
        # Set session
        session['user_id'] = user_id
        session['google_id'] = idinfo['sub']
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'name': idinfo['name'],
                'email': idinfo['email'],
                'picture': idinfo.get('picture')
            }
        })

    except ValueError as e:
        print("Token verification error:", str(e))  # Log verification errors
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        print("General error:", str(e))  # Log general errors
        return jsonify({'error': str(e)}), 500

@auth.route('/auth/google/callback')
def google_callback():
    try:
        # Get the ID token from the request
        token = request.args.get('credential')
        if not token:
            return jsonify({'error': 'No credential received'}), 400

        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            os.getenv('GOOGLE_CLIENT_ID')
        )

        # Get user info from the token
        user_info = {
            'email': idinfo['email'],
            'name': idinfo.get('name', ''),
            'picture': idinfo.get('picture', '')
        }

        # Set session
        session['user'] = user_info

        return jsonify({'success': True, 'user': user_info})

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@auth.route('/auth/logout')
def logout():
    session.clear()
    return jsonify({'success': True})

@auth.route('/auth/user')
def get_current_user():
    if 'user_id' not in session:
        return jsonify(None)
        
    user_model = UserModel()
    user = user_model.get_user(session['google_id'])
    return jsonify(user)