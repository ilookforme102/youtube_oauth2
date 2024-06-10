from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
from datetime import datetime, timedelta,time
from sqlalchemy import Date,Time,DateTime , and_, func, case

from config import app, db
from model.db_schema import User
from flask import request
# def get_user_role():
#     username = session['username']
#     query = db.session.query (User.role).filter(User.username == username).all()
#     data = [{'role': i.role} for i in query]
#     user_role =  data[0]['role']
#     return username
user_bp = Blueprint('user_bp', __name__, url_prefix='/user')
@user_bp.route('/get_user_name_list', methods=['GET'])
def get_all_names():
    """
    Retrieves all users from the User table.

    Returns:
        If the retrieval is successful, returns a JSON response with the user information and a status code of 200.
        If the retrieval fails, returns a JSON response with an error message and a status code of 500.
    """
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Permission required!'}), 403

    users = User.query.all()
    user_data = [user.username for user in users]
    
    return jsonify(user_data), 200
@user_bp.route('/get_all_users', methods=['GET'])
def get_all_users():
    """
    Retrieves all users from the User table.

    Returns:
        If the retrieval is successful, returns a JSON response with the user information and a status code of 200.
        If the retrieval fails, returns a JSON response with an error message and a status code of 500.
    """
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    users_total =   User.query.with_entities(func.count(User.id)).scalar()

    users = User.query.paginate(page=page, per_page=per_page)
    user_data = [{'username': user.username, 'password': user.password, 'role': user.role, 'company_name': user.company_name, 'company_id': user.company_id, 'team': user.team, 'is_active': user.is_active} for user in users.items]
    if page > users.pages:
        return jsonify({'error': 'Invalid page number'}), 400
    else:
        return jsonify({'items': user_data, 'per_page': users.per_page, 'page': users.page,'total_items': users_total}), 200
@user_bp.route('/create_user', methods=['POST'])
def create_user():
    """
    Creates a new user if the logged in user has the role 'admin'.

    Returns:
        If the user creation is successful, returns a JSON response with a success message and a status code of 200.
        If the user creation fails due to missing username or password, returns a JSON response with an error message and a status code of 400.
        If the user creation fails due to the logged in user not having the role 'admin', returns a JSON response with an error message and a status code of 403.
    """
    # username = None
    if 'username' in session:
        # admin_username = session['username']
        user_role = session['role']
    else:
        print('Username not found in session')
    if 'username' not in session or user_role != 'admin':
        return jsonify({'error': 'Permission required!'}), 403
    if request.method == 'POST':
        new_username = request.form.get('username')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        company_id = request.form.get('company_id')
        is_active = request.form.get('is_active')
        team = request.form.get('team')
        role = request.form.get('role')

        if not new_username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        new_user = User(username=new_username, 
                        password=password, 
                        role=role,
                        company_name=company_name, 
                        company_id=company_id, 
                        team=team, 
                        is_active=is_active)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User created successfully'}), 200

    return jsonify({'error': 'Method not allowed'}), 405
@user_bp.route('/edit_user/<username>', methods=['PUT'])
def edit_user(username):
    """
    Edits the information of a user based on their username.
    Args:
        username (str): The username of the user to be edited.
    Returns:
        If the user edit is successful, returns a JSON response with a success message and a status code of 200.
        If the user edit fails due to the logged in user not having the role 'admin', returns a JSON response with an error message and a status code of 403.
        If the user edit fails due to the user not found, returns a JSON response with an error message and a status code of 404.
    """
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Permission required!'}), 403

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if request.method == 'PUT':
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        company_id = request.form.get('company_id')
        is_active = request.form.get('is_active')
        team = request.form.get('team')
        role = request.form.get('role')
        if password:
            user.password = password
        if company_name:
            user.company_name = company_name
        if company_id:
            user.company_id = company_id
        if is_active:
            user.is_active = is_active
        if team:
            user.team = team
        if role:
            user.role = role

        db.session.commit()

        return jsonify({'message': f'User {username} edited successfully'}), 200

    return jsonify({'error': 'Method not allowed'}), 405
@user_bp.route('/delete_user/<username>', methods=['DELETE'])
def delete_user(username):
    """
    Deletes a user based on their username.
    Args:
        username (str): The username of the user to be deleted.
    Returns:
        If the user deletion is successful, returns a JSON response with a success message and a status code of 200.
        If the user deletion fails due to the logged in user not having the role 'admin', returns a JSON response with an error message and a status code of 403.
        If the user deletion fails due to the user not found, returns a JSON response with an error message and a status code of 404.
    """
    if 'username' not in session or session['role'] != 'admin':
        return jsonify({'error': 'Permission required!'}), 403

    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': f'User {username} deleted successfully'}), 200
@user_bp.route('/login', methods=['POST'])
def login():
    """
    Logs in a user by checking the provided username and password.

    Returns:
        If the login is successful, returns a JSON response with a success message and a status code of 200.
        If the login fails due to missing username or password, returns a JSON response with an error message and a status code of 400.
        If the login fails due to an invalid username or password, returns a JSON response with an error message and a status code of 401.
        If the login fails due to unauthenticated login, returns a JSON response with an error message and a status code of 401.
    """
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60)
    user_data = User.query.all()
    users = {user.username: {'password': user.password,'role':user.role} for user in user_data}

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] =  users[username]['role']
            return jsonify({'message': f'Welcome back, {username}'}), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401

    return  jsonify({'error': 'unauthenticated login'}), 401
# Logout endpoint

@user_bp.route('/logout')
def logout():
    session.clear()
    # # session.pop('username', None)
    return jsonify({'message': 'loged out' })