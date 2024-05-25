from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
from flask_cors import CORS,cross_origin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date,Time,DateTime , and_, func, case
import datetime
from datetime import datetime, timedelta
app = Flask(__name__)
app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679'
# Replace the following values with your database connection details
db_username = 'vn168_soc'
db_password = 'YrTBD2CCyXALBPzs'
db_host = '23.226.8.83'
db_database = 'vn168_soc'
db_port = 3306
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_database}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # None, Lax, or Strict
app.config['SESSION_COOKIE_SECURE'] = True  # Should be True if using SameSite=None
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
# app.config['PERMANENT_SESSION_LIFETIME'] =3600*8

# CORS(app, supports_credentials = True)#resources={r"/*": {"origins": "*"}},

CORS(app, supports_credentials = True)

db = SQLAlchemy(app)