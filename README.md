# Secure File Sharing System

A secure file sharing system built with Flask and MongoDB that allows operations users to upload files and client users to download them.

## Features

- Two types of users: Operations and Client
- Secure file upload (pptx, docx, xlsx only)
- Email verification for client users
- Secure file download with temporary links
- JWT-based authentication
- Modern web interface

## Prerequisites

- Python 3.8+
- MongoDB
- SMTP server access for email verification

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd file-sharing-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
MONGODB_URI=mongodb://localhost:27017/file_sharing
JWT_SECRET_KEY=your-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=True
UPLOAD_FOLDER=uploads
```

5. Create the uploads directory:
```bash
mkdir uploads
```

## Running the Application

1. Make sure MongoDB is running on your system

2. Start the Flask application:
```bash
python app.py
```

3. Access the application at `http://localhost:5000`

## Usage

### Operations User

1. Login with operations user credentials
2. Upload files (pptx, docx, xlsx only)

### Client User

1. Sign up with email
2. Verify email through the verification link
3. Login with credentials
4. View and download available files

## Security Features

- Password hashing using bcrypt
- JWT-based authentication
- File type verification
- Temporary download links
- Email verification for new users

## API Endpoints

### Authentication
- POST `/api/auth/ops/login` - Operations user login
- POST `/api/auth/client/signup` - Client user registration
- GET `/api/auth/verify/<token>` - Email verification
- POST `/api/auth/client/login` - Client user login

### File Operations
- POST `/api/files/upload` - Upload file (Operations users only)
- GET `/api/files/list` - List all files (Client users only)
- GET `/api/files/download/<file_id>` - Get download link (Client users only)
- GET `/api/files/download-file/<token>` - Download file with temporary token

## Directory Structure

```
file-sharing-system/
├── app.py
├── requirements.txt
├── .env
├── README.md
├── database/
│   └── db.py
├── routes/
│   ├── auth_routes.py
│   └── file_routes.py
├── static/
│   └── css/
│       └── style.css
├── templates/
│   └── index.html
└── uploads/
```
