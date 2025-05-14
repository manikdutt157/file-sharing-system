from flask import Blueprint, request, jsonify, send_file
from database.db import get_db
from routes.auth_routes import token_required
import os
import magic
from werkzeug.utils import secure_filename
from bson import ObjectId
import uuid
import jwt
import datetime
import traceback

file_bp = Blueprint('file', __name__)

ALLOWED_EXTENSIONS = {'pptx', 'docx', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@file_bp.route('/test-upload-dir', methods=['GET'])
def test_upload_dir():
    try:
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        
        # Check if directory exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            return jsonify({
                'message': f'Created upload directory: {upload_folder}',
                'exists': True,
                'writable': os.access(upload_folder, os.W_OK)
            })
            
        return jsonify({
            'message': f'Upload directory exists: {upload_folder}',
            'exists': True,
            'writable': os.access(upload_folder, os.W_OK),
            'absolute_path': os.path.abspath(upload_folder)
        })
    except Exception as e:
        return jsonify({
            'message': f'Error checking upload directory: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@file_bp.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    if current_user['user_type'] != 'ops':
        return jsonify({'message': 'Unauthorized'}), 403
    
    # Print debug information
    print("Request files:", request.files)
    print("Request form:", request.form)
    print("Content type:", request.content_type)
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{str(uuid.uuid4())}_{filename}"
        upload_folder = os.getenv('UPLOAD_FOLDER', 'uploads')
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        print(f"Saving file to: {file_path}")
        
        # Save the file
        file.save(file_path)
        print(f"File saved successfully to {file_path}")
        
        # Verify file type using python-magic
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)
        print(f"Detected file type: {file_type}")
        
        if not any(ext in file_type for ext in ['officedocument', 'spreadsheet', 'presentation']):
            os.remove(file_path)
            return jsonify({'message': 'Invalid file type'}), 400
        
        file_record = {
            'filename': filename,
            'stored_filename': unique_filename,
            'uploaded_by': str(current_user['_id']),
            'upload_date': datetime.datetime.utcnow(),
            'file_type': file_type
        }
        
        result = get_db().files.insert_one(file_record)
        print(f"File record created with ID: {result.inserted_id}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': str(result.inserted_id)
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'message': f'Error during upload: {str(e)}'}), 500

@file_bp.route('/list', methods=['GET'])
@token_required
def list_files(current_user):
    if current_user['user_type'] != 'client':
        return jsonify({'message': 'Unauthorized'}), 403
    
    files = list(get_db().files.find())
    for file in files:
        file['_id'] = str(file['_id'])
    
    return jsonify({'files': files})

@file_bp.route('/download/<file_id>', methods=['GET'])
@token_required
def download_file(current_user, file_id):
    if current_user['user_type'] != 'client':
        return jsonify({'message': 'Unauthorized'}), 403
    
    try:
        file_record = get_db().files.find_one({'_id': ObjectId(file_id)})
        if not file_record:
            return jsonify({'message': 'File not found'}), 404
        
        file_path = os.path.join(os.getenv('UPLOAD_FOLDER'), file_record['stored_filename'])
        if not os.path.exists(file_path):
            return jsonify({'message': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=file_record['filename'])
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@file_bp.route('/download-file/<token>', methods=['GET'])
def download_file_with_token(token):
    try:
        data = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
        file_record = get_db().files.find_one({'_id': ObjectId(data['file_id'])})
        
        if not file_record:
            return jsonify({'message': 'File not found'}), 404
        
        file_path = os.path.join(os.getenv('UPLOAD_FOLDER'), file_record['stored_filename'])
        return send_file(file_path, as_attachment=True, download_name=file_record['filename'])
        
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Download link expired'}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500 