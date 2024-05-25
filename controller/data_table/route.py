from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
from config import app,db
data_table_bp = Blueprint('data_table_bp', __name__, url_prefix='/data_table')
from flask_cors import CORS

CORS(app, supports_credentials = True)

@data_table_bp.route('/create_tables')
def create_tables():
    with app.app_context():
        db.create_all() 
    return 'All tables are created successfully'