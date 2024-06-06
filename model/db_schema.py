from flask import Flask#, jsonify, request, session, make_response,redirect, url_for,Blueprint
from flask_cors import CORS,cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date,Time,DateTime , and_, func, case
from config import app,db
# import datetime
# from datetime import datetime, timedelta
# app = Flask(__name__)
# app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679'
# # Replace the following values with your database connection details
# db_username = 'crm'
# db_password = 'LSciYCtCK7tZXAxL'
# db_host = '23.226.8.83'
# db_database = 'crm'
# db_port = 3306
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_database}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# # app.config['CORS_HEADERS'] = 'Content-Type'
# app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # None, Lax, or Strict
# app.config['SESSION_COOKIE_SECURE'] = True  # Should be True if using SameSite=None
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['CORS_HEADERS'] = 'Content-Type'
# # app.config['PERMANENT_SESSION_LIFETIME'] =3600*8

# # CORS(app, supports_credentials = True)#resources={r"/*": {"origins": "*"}},

# CORS(app, supports_credentials = True)

# db = SQLAlchemy(app)
# Table Creation
class YoutubeVideoData(db.Model):
    __tablename__ = 'db_vn168_soc_yt_video_data'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    video_id =  db.Column(db.String(255), unique = True, nullable = False)
    video_title =  db.Column(db.String(255), nullable = False)
    video_description =  db.Column(db.String(2500), nullable = False)
    published_at =  db.Column(DateTime, nullable = False)
    thumbnail_url =  db.Column(db.String(255), nullable = False)
    channel_name =  db.Column(db.String(255),  nullable = False)
    channel_id =  db.Column(db.String(255),  nullable = False)
    playlist_id = db.Column(db.String(255),  nullable = True)
class YoutubeData(db.Model):
    __tablename__ = 'db_vn168_soc_yt_data'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id =  db.Column(db.String(255), unique = True, nullable = False)
    channel_id =  db.Column(db.String(255), unique = True, nullable = False)
    channel_name =  db.Column(db.String(255), nullable = False)
    # user_name =  db.Column(db.String(255), nullable = False)
    user_email =  db.Column(db.String(255), unique = True, nullable = False)
    refresh_token =  db.Column(db.String(255), unique = True, nullable = False)
    person_in_charge = db.Column(db.String(255),  nullable = True)
class GoogleAccount(db.Model):
    __tablename__ = 'db_vn168_soc_yt_user'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    user_id =  db.Column(db.String(255), unique = True, nullable = False)
    # user_name =  db.Column(db.String(255), nullable = False)
    user_email =  db.Column(db.String(255), unique = True, nullable = False)
    refresh_token =  db.Column(db.String(255), unique = True, nullable = False)
    person_in_charge = db.Column(db.String(255), unique = True, nullable = False)
    # def __repr__(self):
    #     return f'<User {self.user_name}>'
class YoutubeChannel(db.Model):
    __tablename__ = 'db_vn168_soc_yt_channel'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    channel_id =  db.Column(db.String(255), unique = True, nullable = False)
    channel_name =  db.Column(db.String(255), nullable = False)
    user_id =  db.Column(db.String(255), unique = True, nullable = False)
    # person_in_charge = db.Column(db.String(255), unique = True, nullable = False)
class FacebookAccount(db.Model):
    __tablename__ = 'db_vn168_soc_fb_account'
    id = db.Column(db.Integer, primary_key = True,autoincrement = True)
    user_id =  db.Column(db.String(255), unique = True, nullable = False)
    user_name =  db.Column(db.String(255), nullable = False)
    short_live_user_token =  db.Column(db.String(255), unique = True, nullable = False)
    long_live_user_token =  db.Column(db.String(255), unique = True, nullable = False)
    token_expired_date =  db.Column(DateTime, unique = True, nullable = False)
    person_in_charge = db.Column(db.String(255), unique = True, nullable = False)
class FacebookPage(db.Model):
    __tablename__ = 'db_vn168_soc_fb_page'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    page_id =  db.Column(db.String(255), unique = True, nullable = False)
    page_name =  db.Column(db.String(255), nullable = False)
    long_live_page_token =  db.Column(db.String(255), unique = True, nullable = False)
    user_id  =  db.Column(db.String(255), unique = True, nullable = False)
    person_in_charge = db.Column(db.String(255), unique = True, nullable = False)
class User(db.Model):
    __tablename__ = 'db_vn168_soc_user'
    id = db.Column(db.Integer, primary_key = True,autoincrement = True)
    username =  db.Column(db.String(255), nullable = False, unique = True)
    password = db.Column(db.String(255), nullable = False)
    company_name = db.Column(db.String(255), nullable = False)
    company_id = db.Column(db.String(255), nullable = False, unique = True)
    is_active = db.Column(db.Boolean, default = True)
    role = db.Column(db.String(255), nullable = False)
    team = db.Column(db.String(255), nullable = False)