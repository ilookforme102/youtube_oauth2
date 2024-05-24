from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
fb_bp = Blueprint('fb_bp', __name__, url_prefix='/facebook')