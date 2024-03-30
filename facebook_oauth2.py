from flask import Flask, request, redirect, session
import requests
app = Flask(__name__)
app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679' #auto generate
#IDs for the app
CLIENT_SECRET = 'cb10b0592db22018171a652375a7513a'
CLIENT_ID = '1476099873250266' #AKA app id
REDIRECT_URI = 'http://localhost:5000/callback'
@app.route('/')
def home_page():
    return redirect(f'https://www.facebook.com/dialog/oauth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=email')
if __name__ == '__main__':
    app.run('localhost', 5000, debug=True)