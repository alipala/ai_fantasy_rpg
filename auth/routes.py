from google.oauth2 import id_token
from google.auth.transport import requests
from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for, send_file, Response
import os
from auth.models import UserModel
import datetime

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

@auth.route('/api/placeholder/<int:width>/<int:height>')
def placeholder_image(width: int, height: int):
    """Generate a simple placeholder image"""
    try:
        from PIL import Image, ImageDraw
        import io
        
        # Limit dimensions for security
        width = min(width, 1024)
        height = min(height, 1024)

        # Create base image
        img = Image.new('RGB', (width, height), color='#2a2a3d')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple pattern instead of text
        margin = min(width, height) // 10
        draw.rectangle(
            [margin, margin, width - margin, height - margin],
            outline='#ffffff',
            width=2
        )
        draw.line([(margin, margin), (width - margin, height - margin)], fill='#ffffff', width=2)
        draw.line([(margin, height - margin), (width - margin, margin)], fill='#ffffff', width=2)
        
        # Save to buffer
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        
        # Removed cache_timeout parameter
        return send_file(
            img_io, 
            mimetype='image/png'
        )
        
    except Exception as e:
        print(f"Placeholder image error: {e}")
        # Return simple colored rectangle as fallback
        return Response(
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            mimetype='image/png'
        )

@auth.route('/add-victory', methods=['POST'])
def add_victory():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    try:
        victory_data = request.json
        user_model = UserModel()
        success = user_model.add_victory(session['user_id'], victory_data)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Failed to store victory"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@auth.route('/gallery')
def gallery():
    if 'user_id' not in session:
        return redirect(url_for('home'))
        
    page = request.args.get('page', 1, type=int)
    user_model = UserModel()
    
    gallery_data = user_model.get_user_victories(session['user_id'], page)
    
    # Format dates for display
    for victory in gallery_data.get('victories', []):
        if isinstance(victory.get('created_at'), str):
            victory['created_at'] = datetime.fromisoformat(victory['created_at'])
    
    # Add user data
    user = user_model.get_user(session['google_id'])
    
    # Check if empty
    empty = not gallery_data.get('victories', [])
    
    return render_template('victory-album.html', 
                         gallery_data=gallery_data,
                         current_page=page,
                         user=user,
                         empty=empty)

@auth.route('/add-completion', methods=['POST'])
def add_completion():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    try:
        data = request.json
        user_model = UserModel()
        user_model.add_completion(session['user_id'], data.get('completion_id'))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500