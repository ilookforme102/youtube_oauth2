from flask import Flask, jsonify, request, session, make_response,redirect, url_for, Blueprint
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date,Time,DateTime , and_, func, case
import datetime
from controller.facebook.route import fb_bp
from controller.youtube.route import yt_bp
from controller.user.route import user_bp
from controller.data_table.route import data_table_bp
from model.db_schema import YoutubeChannel,GoogleAccount, FacebookAccount, FacebookPage
from config import app, db
# from flask_session import Session
# Session(app)
CORS(app, supports_credentials= True)
# @app.before_request
# def check_authentication():
#     #skip authorization for the optiohns method bcz it doesnt has cookie
#     if request.method != "OPTIONS":
        
#         session_cookie = request.cookies.get('session') 
#         if request.endpoint != 'user_bp.login' and 'username' not in session and session_cookie != True:
#             return jsonify({'error': 'unauthenticated'}), 401#redirect(url_for('login'))
#     else: 
#         headers = {
#             'Access-Control-Allow-Origin': '*',  # Replace with your frontend domain
#             'Access-Control-Allow-Methods': 'PUT, DELETE',
#             'Access-Control-Allow-Headers': 'Content-Type',
#             'Access-Control-Max-Age': '3600',  # Cache preflight response for 1 hour
#             'Access-Control-Allow-Credentials': 'true'
#         }
#         return ('', 204, headers)
app.register_blueprint(data_table_bp)
app.register_blueprint(fb_bp)
app.register_blueprint(yt_bp)
app.register_blueprint(user_bp)
if __name__ == '__main__':
    app.run(port=5000, debug=True)