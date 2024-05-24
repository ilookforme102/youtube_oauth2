from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
yt_bp = Blueprint('yt_bp', __name__, url_prefix='/youtube')
from flask import Flask, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from model.db_schema import app, db, User, GoogleAccount, YoutubeChannel, FacebookAccount, FacebookPage
import datetime
import json
import os
import requests
import pymysql
########MySQL###############
host='128.199.228.235'
user='sql_dabanhtructi'
password='FKb75AYJzFMJET8F'
database='sql_dabanhtructi'
port = 3306
def get_data(sql):
    conn = pymysql.connect(
            host='128.199.228.235', 
            user='sql_dabanhtructi', 
            password='FKb75AYJzFMJET8F', 
            database='sql_dabanhtructi',
            port = 3306)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
         # Fetch all the rows in a list of lists.
        rows = cursor.fetchall()
        return list(rows)
    except pymysql.OperationalError as e:
        if e.args[0] in (2006,2003, 2013):
            print("Lost connection, attempting to reconnect...")
            conn.ping(reconnect=True)
            cursor.execute(sql)
            rows = cursor.fetchall()
            return list(rows)
        else:
            print("An error occurred:", e)
            conn.rollback()
    except Exception as e:
        print(e)
        conn.rollback()
    finally:
        conn.close()
##############################################
# {"web":{"client_id":"236896140259-jte4kc2hfp0cfki0qi00bjkmscj9k92r.apps.googleusercontent.com",
#         "project_id":"digichrom-1698819902733",
#         "auth_uri":"https://accounts.google.com/o/oauth2/auth",
#         "token_uri":"https://oauth2.googleapis.com/token",
#         "auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs",
#         "client_secret":"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",
#     "redirect_uris":["http://localhost:3000/youtube/oauth2callback"]}}
app = Flask(__name__)
app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679'  # Needed for session tracking
channel_ids = []
# Google OAuth 2.0 Client ID and Secret
CLIENT_SECRETS_FILE = "cred3.json"
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',  # To access YouTube channel data
    'https://www.googleapis.com/auth/userinfo.email',    # To access the user's email address
    'https://www.googleapis.com/auth/userinfo.profile'   # To access the user's profile information, including ID
]
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # ONLY for development
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
channel_ids = []
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
## Save all key, value pairs in Session credentials to the Credentials object
## Reverse the session object back to the Credentials
def session_to_credentials(session):
    return Credentials(
        token=session['token'],
        refresh_token=session['refresh_token'],
        token_uri=session['token_uri'],
        client_id=session['client_id'],
        client_secret=session['client_secret'],
        scopes=session['scopes'])
@yt_bp.route('/')
def index():
    # Check if the user is authenticated
    if 'credentials' not in session:
        return '<a href="/youtube/authorize">Authorize Access to YouTube</a>'
    # User is authenticated, proceed with API calls
    return redirect("/fetch_youtube_metrics")

@yt_bp.route('/authorize')
def authorize():
    # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    #The flow object is used to generate an authorization URL to which the user will be 
    #redirected. This URL directs the user to Google's OAuth 2.0 server, 
    #where they can authorize your application to access their Google data 
    #according to the scopes you've requested.
    session.clear()
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        #Declare the url to redirect to after authorize my application to access their Google data
        redirect_uri='https://soc.168dev.com/youtube/oauth2callback')
    # authorization_url is url to redirect to from /authorize
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true', prompt = 'consent')

    # Store the state in the session so you can verify the callback
    session['state'] = state
    # At this url, server will redicrect user to Google's OAuth 2.0 server
    return redirect(authorization_url)
    # oauth2callback()
    #soc.168dev.com/youtube/
@yt_bp.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback to verify the authorization server response
    state = session['state']

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state,
        redirect_uri='https://soc.168dev.com/youtube/oauth2callback'))

    authorization_response = request.url
    # Fet_token method is being used to exchange client secret with refresh token
    flow.fetch_token(authorization_response=authorization_response)
    #At this point flow.credentials only have value of access token and refresh token under flow.credentials.token
    # and flow.credentials.refresh_token
    credentials = flow.credentials
    #Convert credentials into a python dictionary 
    #as same datatype of session object
    session['credentials'] = credentials_to_dict(credentials)

    # Print out the refresh token
    # print(f"Refresh Token: {credentials.refresh_token}")
    # return credentials_to_dict(credentials)
    return jsonify(session['credentials'])#redirect("https://5goal.club/tin-the-thao/esports")#'Authorization complete. Check the console for the refresh token.'
# The reason to get access token is that it  only valid for a couple minutes 
# so everytime we want to get data from user, we have to use refresh token to get the access token
# Request new access token at https://oauth2.googleapis.com/token

@yt_bp.route('/get_access_token')
def get_access_token():
    current_credentitals = session['credentials']
    refresh_token = current_credentitals['refresh_token']
    client_id = current_credentitals['client_id']
    client_secret = current_credentitals['client_secret']
    request_url  = 'https://oauth2.googleapis.com/token'
    request_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    response = requests.post(request_url, data=request_data)
    response_data = response.json()
    new_access_token = response_data.get('access_token')
    session['credentials']['token']=  new_access_token
    return new_access_token

@yt_bp.route('/gg_save_user_info', methods = ['GET','OPTIONS'])
def gg_save_user_info():
    if 'credentials' not in session:
        return redirect('authorize')
    credentials = session_to_credentials(session['credentials'])
    #Get user id and email
    oauth2_service = build('oauth2', 'v2', credentials=credentials)

    # Get user information
    user_info = oauth2_service.userinfo().get().execute()
    user_id = user_info.get('id')
    session['user_id']= user_id
    user_email = user_info.get('email')
    # session['user_email']= user_email
    user_name = user_info.get('name')
    # session['user_name']= user_name
    refresh_token =  session['credentials']['refresh_token']
    # if Goo
    # conn = pymysql.connect(host=host,user=user, password=password, database=database,port=port)
    # try:
    # # Create a cursor object
    #     with conn.cursor() as cursor:
    #         # SQL INSERT statement
    #         sql = "INSERT INTO `db_gg_user` (`user_id`, `user_name`, `user_email`, `refresh_token`) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `user_id` = VALUES(`user_id`),`user_name` = VALUES(`user_name`),`user_email` = VALUES(`user_email`),`refresh_token` = VALUES(`refresh_token`)"
            
    #         # Values to insert
    #         values = (user_id, user_name, user_email,refresh_token)
            
    #         # Execute the SQL statement
    #         cursor.execute(sql, values)
            
    #         # Commit the transaction
    #         conn.commit()
            
    #         print("Values inserted successfully.")
            
    # except pymysql.MySQLError as e:
    #     print(f"Error: {e}")
        
    # finally:
    #     # Close the connection
    #     conn.close()
    # return "Your data is fucking stolen!!"
    # return redirect('/gg_save_page_info')
@yt_bp.route('/gg_save_page_info')
def gg_save_page_info():
    if 'credentials' not in session:
        return redirect('authorize')
    
    credentials = session_to_credentials(session['credentials'])
    # user__id = session['user_id']
    #get channel id
    youtube = build('youtube', 'v3', credentials=credentials)
    request = youtube.channels().list(
        part='id,snippet,contentDetails,statistics',
        mine=True
    )
    response = request.execute()
    conn = pymysql.connect(host=host, user = user, password= password, database = database, port=port)
    try:
        with conn.cursor() as cursor:
            for item in response.get('items', []):
                owner_id = session['user_id']
                channel_id = item['id']
                channel_name  =  item['snippet']['title']
                sql = "INSERT INTO `db_gg_channel` (`channel_id`, `channel_name`,`owner_id`) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE `channel_id` = VALUES(`channel_id`),`channel_name` = VALUES(`channel_name`),`owner_id` = VALUES(`owner_id`)"
                
                # Values to insert
                values = (channel_id, channel_name,owner_id)
                
                # Execute the SQL statement
                cursor.execute(sql, values)
                
                # Commit the transaction
                conn.commit()
                
                print("Values inserted successfully.")
            

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
    finally:
        # Close the connection
        conn.close()
    return response
###################################################################
#####Below are the endponts use to get data from database only#####
###################################################################
def load_client_credentials(json_filepath):
    """Load client_id and client_secret from a credentials.json file."""
    with open(json_filepath, 'r') as file:
        data = json.load(file)
    
    client_id = data['web']['client_id']
    client_secret = data['web']['client_secret']
    token_uri = data['web']['token_uri']
    return client_id, client_secret, token_uri

# Fixed variables
client_id, client_secret, token_uri = load_client_credentials(CLIENT_SECRETS_FILE)
#####################################################################
##write some functions to extract parameters from specigfic channel
##endpoints create here only for testing purpose
######################################################################
#get refresh token
def get_refresh_token(channel_name):
    sql = '''SELECT c.channel_id, u.refresh_token 
    FROM `db_gg_channel` as c 
    INNER JOIN `db_gg_user` u 
    ON c.owner_id = u.user_id 
    WHERE channel_name = "{channel_name}";'''.format(channel_name = channel_name)
    rows = get_data(sql)
    refresh_token = rows[0][1]
    channel_id = rows[0][0]
    return refresh_token,channel_id
refresh_token,channel_id = get_refresh_token("Shang Uchiha")
def access_token_generate(refresh_token):
    request_url = 'https://oauth2.googleapis.com/token'
    request_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    response = requests.post(request_url, data=request_data)
    response_data = response.json()
    return response_data.get('access_token')
temp_access_token = access_token_generate(refresh_token)
#Create Credentials object
def credentials_generate(access_token, refresh_token,token_uri,client_id,client_secret):
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES)
@yt_bp.route('/list_channels')
def list_channels():
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    oauth2_service = build('oauth2', 'v2', credentials=credentials)

    # Get user information
    user_info = oauth2_service.userinfo().get().execute()

    user_id = user_info.get('id')
    user_email = user_info.get('email')
        
    #get channel id
    youtube = build('youtube', 'v3', credentials=credentials)
    request = youtube.channels().list(
        part='id,snippet,contentDetails,statistics',
        mine=True
    )
    response = request.execute()

    channels = []
    for item in response.get('items', []):
        channels.append({
            'name': item['snippet']['title'],
            'id': item['id'],
            'user_id':user_id,
            'user_email':user_email
            
        })
        
    return jsonify(channels)
#test a get method to return insights metrics 
#for a specific channel   
@yt_bp.route('/get_channel_metrics')
def get_channel_metrics():
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    # Build the YouTube Analytics service object
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    # Define the date range for the last 30 days
    end_date = datetime.date.today().isoformat()
    start_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()

    # Fetch YouTube Analytics data
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics='estimatedMinutesWatched,views,likes,subscribersGained',
        dimensions='day',
        sort = 'day'
    ).execute()
    return jsonify(response)
###########################################################
#########POST METHOD:
#########Get the channel as parameter and returns time serries data about
#########channel insights, you can find all the neccessary metrics from meta API website
#########Postman test - Body -Raw :  {"channel_name":"Shang Uchiha"}
@yt_bp.route('/insights', methods = ['POST'])
def insights():
    data = request.json
    channel_name = data.get('channel_name')
    refresh_token, channel_id = get_refresh_token(channel_name)
    temp_access_token = access_token_generate(refresh_token)
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    # Define the date range for the last 30 days
    # end_date = datetime.date.today().isoformat()
    # start_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    # Date format: yyyy-mm-dd
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    # Fetch YouTube Analytics data
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics='estimatedMinutesWatched,views,likes,subscribersGained',
        dimensions='day',
        sort = 'day'
    ).execute()
    return jsonify(response)
@yt_bp.route('/test')
def test(): 
    end_date = datetime.date.today().isoformat()

#SELECT * FROM `db_gg_channel` as c INNER JOIN `db_gg_user` u ON c.owner_id = u.user_id WHERE channel_name = "Shang Uchiha";
    return end_date
@yt_bp.route('/get_channel_insights')
def get_channel_insights():
    channel_name = "Shang Uchiha"
    sql = '''SELECT c.channel_id, u.refresh_token FROM `db_gg_channel` as c 
            INNER JOIN `db_gg_user` u 
            ON c.owner_id = u.user_id 
            WHERE channel_name = "{channel_name}";'''.format(channel_name= channel_name)
    rows = get_data(sql)
    channel_id = rows[0][0]
    return rows
# if __name__ == '__main__':
#     app.run('localhost', port= 3000, debug=True)
