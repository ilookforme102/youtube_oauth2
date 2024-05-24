from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
from datetime import datetime, timedelta,time
from config import app, db
from model.db_schema import User

user_bp = Blueprint('user_bp', __name__, url_prefix='/user')
@user_bp.route('/login', methods=['POST', 'GET'])
def login():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)
    user_data = User.query.all()
    users = {user.username: {'password': user.password} for user in user_data}

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        if username in users and users[username]['password'] == password:
            session['username'] = username

            return jsonify({'error': 'unauthenticated login'}), 401
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    return  jsonify({'error': 'unauthenticated login'}), 401
# Logout endpoint
@user_bp.route('/logout')
def logout():
    session.clear()
    # # session.pop('username', None)
    return jsonify({'message': 'loged out' })