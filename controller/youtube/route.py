from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
yt_bp = Blueprint('yt_bp', __name__, url_prefix='/youtube')
from flask import Flask, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from model.db_schema import app, db, User, GoogleAccount, YoutubeChannel,YoutubeData, FacebookAccount,YoutubeVideoData, FacebookPage
from controller.youtube.service import credentials_to_dict,session_to_credentials, load_client_credentials,get_refresh_token,access_token_generate,credentials_generate,get_video_titles,get_all_videos,get_video_comments,comment_classification
      
import datetime
from datetime import datetime
import time
import json
import os
import requests
import pymysql
import os
from dotenv import load_dotenv
import re
load_dotenv()
#############################
# db_username = 'vn168_soc'
# db_password = 'YrTBD2CCyXALBPzs'
# db_host = '23.226.8.83'
# db_database = 'vn168_soc'
# db_port = 3306
# app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_username}:{db_password}@{db_host}/{db_database}'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
########MySQL###############
host='23.226.8.83'
user='vn168_soc'
password='YrTBD2CCyXALBPzs'
database='vn168_soc'
port = 3306
def get_data(sql):
    conn = pymysql.connect(
            host=host, 
            user= user, 
            password=password, 
            database=database,
            port = port)
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
    'https://www.googleapis.com/auth/userinfo.profile' ,  # To access the user's profile information, including ID
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # ONLY for development
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
channel_ids = []

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
    # session.clear()
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        #Declare the url to redirect to after authorize my application to access their Google data
        redirect_uri= os.getenv('OAUTH2_REDIRECT_URI'))
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
        redirect_uri=os.getenv('OAUTH2_REDIRECT_URI'))

    authorization_response = request.url
    # Fet_token method is being used to exchange client secret with refresh token
    flow.fetch_token(authorization_response=authorization_response)
    #At this point flow.credentials only have value of access token and refresh token under flow.credentials.token
    # and flow.credentials.refresh_token
    credentials = flow.credentials
    session['yt_credentials'] = credentials_to_dict(credentials)
    oauth2_service = build('oauth2', 'v2', credentials=credentials)
    # Get user information
    user_info = oauth2_service.userinfo().get().execute()
    user_id = user_info.get('id')
    session['user_id']= user_id
    user_email = user_info.get('email')
    # session['user_email']= user_email
    # user_name = user_info.get('name')
    # session['user_name']= user_name
    refresh_token =  session['yt_credentials']['refresh_token']
    #Convert credentials into a python dictionary 
    #as same datatype of session object
    # if YoutubeChannel.query.filter(YoutubeChannel.channel_id ==channel_id).all():
    #     return redirect(url_for("yt_bp.authorize"))
    if YoutubeData.query.filter(YoutubeData.user_id ==user_id).all():
        return redirect(url_for("yt_bp.authorize"))
    youtube = build('youtube', 'v3', credentials=credentials)
    api_request = youtube.channels().list(
        part='id,snippet,contentDetails,statistics',
        mine=True
    )
    response = api_request.execute()
    for item in response.get('items', []):
        person_in_charge = session['username']
        channel_id = item['id']
        channel_name  =  item['snippet']['title']
        if YoutubeData.query.filter(YoutubeData.channel_id ==channel_id).all():
            return redirect(url_for("yt_bp.authorize"))
        new_channel = YoutubeData(
            user_id = user_id,
            channel_id =  channel_id,
            channel_name =channel_name,
            user_email = user_email,
            refresh_token = refresh_token,
            person_in_charge = person_in_charge
            
        )
        db.session.add(new_channel)
    db.session.commit()
    after_callback = os.getenv('CALLBACK_REDIRECT_URL')
    return redirect(after_callback)
    
    # after_callback = os.getenv('CALLBACK_REDIRECT_URL')
    # return jsonify({'name':user_name,'email':user_email,'user_id':user_id,'refresh_token':refresh_token})
    # return redirect(after_callback)
    # Print out the refresh token
    # print(f"Refresh Token: {credentials.refresh_token}")
    # return credentials_to_dict(credentials)
    # return jsonify(session['yt_credentials'])#redirect("https://5goal.club/tin-the-thao/esports")#'Authorization complete. Check the console for the refresh token.'
# The reason to get access token is that it  only valid for a couple minutes 
# so everytime we want to get data from user, we have to use refresh token to get the access token
# Request new access token at https://oauth2.googleapis.com/token
@yt_bp.route('/get_credentials')
def get_credentials():
    return session['yt_credentials']
####generating new access token
@yt_bp.route('/get_access_token')
def get_access_token():
    current_credentitals = session['yt_credentials']
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
    session['yt_credentials']['token']=  new_access_token
    return new_access_token

@yt_bp.route('/gg_save_user_info', methods = ['GET','OPTIONS'])
def gg_save_user_info():
    if 'credentials' not in session:
        return redirect('authorize')
    credentials = session_to_credentials(session['yt_credentials'])
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
    refresh_token =  session['yt_credentials']['refresh_token']
    if GoogleAccount.query.filter(GoogleAccount.user_id == user.user_id).all():
        return jsonify({"error": "Device info is already existed, please try again"}), 409
    new_user = GoogleAccount(
        user_id = user_id,
        user_email =  user_email,
        refresh_token = refresh_token,
        person_in_charge = user_name

    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User data added successfully','data': user_email}), 200
   
@yt_bp.route('/gg_save_channel_info')
def save_channel_info():
    if 'credentials' not in session:
        return redirect('authorize')
    
    credentials = session_to_credentials(session['yt_credentials'])
    # user__id = session['user_id']
    #get channel id
    youtube = build('youtube', 'v3', credentials=credentials)
    request = youtube.channels().list(
        part='id,snippet,contentDetails,statistics',
        mine=True
    )
    response = request.execute()
    for item in response.get('items', []):
        owner_id = session['user_id']
        channel_id = item['id']
        channel_name  =  item['snippet']['title']
        new_channel = YoutubeChannel(
            channel_id =  channel_id,
            channel_name =channel_name,
            user_id =owner_id,
        )
        db.session.add(new_channel)
        db.session.commit()
    return jsonify({'message': 'Channel data added successfully'}), 200    
# def gg_save_page_info():
#     if 'credentials' not in session:
#         return redirect('authorize')
    
#     credentials = session_to_credentials(session['yt_credentials'])
#     # user__id = session['user_id']
#     #get channel id
#     youtube = build('youtube', 'v3', credentials=credentials)
#     request = youtube.channels().list(
#         part='id,snippet,contentDetails,statistics',
#         mine=True
#     )
#     response = request.execute()
#     conn = pymysql.connect(host=host, user = user, password= password, database = database, port=port)
#     try:
#         with conn.cursor() as cursor:
#             for item in response.get('items', []):
#                 owner_id = session['user_id']
#                 channel_id = item['id']
#                 channel_name  =  item['snippet']['title']
#                 sql = "INSERT INTO `db_vn168_soc_yt_channel` (`channel_id`, `channel_name`,`user_id`) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE `channel_id` = VALUES(`channel_id`),`channel_name` = VALUES(`channel_name`),`owner_id` = VALUES(`owner_id`)"
                
#                 # Values to insert
#                 values = (channel_id, channel_name,owner_id)
                
#                 # Execute the SQL statement
#                 cursor.execute(sql, values)
                
#                 # Commit the transaction
#                 conn.commit()
                
#                 print("Values inserted successfully.")
            

#     except pymysql.MySQLError as e:
#         print(f"Error: {e}")
#     finally:
#         # Close the connection
#         conn.close()
#     return response
###################################################################
#####Below are the endponts use to get data from database only#####
###################################################################


# Fixed variables
client_id, client_secret, token_uri = load_client_credentials(CLIENT_SECRETS_FILE)

@yt_bp.route('/list_channels')
def get_channel_list():
    data = request.args
    
    results = db.session.query(
        YoutubeData.channel_id, 
        YoutubeData.channel_name,
        YoutubeData.person_in_charge
    ).all()
    channel_data = [{'channel_name': result.channel_name,
             'channel_id': result.channel_id, 
             'person_in_charge': result.person_in_charge} for result in results]
    try:
        page = int(data.get('page',1))
        per_page = int(data.get('per_page',10))
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_data = channel_data[start_index:end_index]
        return jsonify({'items':paginated_data,'page':page,'per_page':per_page, 'total_items':len(channel_data)})
    except TypeError:
        return jsonify({'items':channel_data,'page':1,'per_page':len(channel_data), 'total_items':len(channel_data)})
@yt_bp.route("/list_channel_name")
def get_list_channel_name():
    results = db.session.query(
        YoutubeData.channel_name
    ).all()
    data = [result.channel_name for result in results]
    return jsonify(data)
@yt_bp.route('/edit_list_channel/<string:channel_id>', methods=['PUT','OPTIONS'])
def edit_list_channel(channel_id):
    data = request.form
    person_in_charge = data.get('person_in_charge')
    
    # Update the person_in_charge column in the database
    youtube_data = YoutubeData.query.filter(YoutubeData.channel_id==channel_id).first()
    if youtube_data:
        youtube_data.person_in_charge = person_in_charge
        db.session.commit()
        return jsonify({'message': 'Person in charge updated successfully'})
    else:
        return jsonify({'message': 'Channel not found'})
# def get_refresh_tokens():
#     data = request.args
#     channel_name = data.get("channel_name")
#     results = db.session.query(
#         YoutubeData.channel_id, 
#         YoutubeData.refresh_token
#     ).filter(
#         YoutubeData.channel_name == channel_name
#     ).all()
#     if not results:
#         return jsonify({'message':'no record found'}),404
#     data = [{'channel_id': result.channel_id, 'refresh_token':result.refresh_token} for result in results]
#     # channel_id = data[0]['channel_id']
#     # refresh_token = data[0]['refresh_token']
#     return jsonify(data)
#test a get method to return insights metrics 
#for a specific channel   
# @yt_bp.route('/get_channel_metrics')
# def get_channel_metrics():
#     data = request.args
#     channel_name = data.get("channel_name")
#     results = db.session.query(
#         YoutubeData.channel_id, 
#         YoutubeData.refresh_token
#     ).filter(
#         YoutubeData.channel_name == channel_name
#     ).all()
#     if not results:
#         return jsonify({'message':'no record found'}),404
#     data = [{'channel_id': result.channel_id, 'refresh_token':result.refresh_token} for result in results]
#     # channel_id = data[0]['channel_id']
#     # refresh_token = data[0]['refresh_token']
#     credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
#     # Build the YouTube Analytics service object
#     youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
#     # Define the date range for the last 30 days
#     end_date = datetime.date.today().isoformat()
#     start_date = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()

#     # Fetch YouTube Analytics data
#     response = youtubeAnalytics.reports().query(
#         ids=f'channel=={channel_id}',
#         startDate=start_date,
#         endDate=end_date,
#         metrics='estimatedMinutesWatched,views,likes,subscribersGained',
#         dimensions='day',
#         sort = 'day'
#     ).execute()
#     return jsonify(response)
###########################################################
#########DELETE METHOD:
#########Get the channel as parameter and returns time serries data about
@yt_bp.route('/list_channels/<string:channel_id>',methods = ['DELETE','OPTIONS'])
def delete_channel(channel_id):
    channel_id =YoutubeData.query.filter(YoutubeData.channel_id == channel_id).first()
    if channel_id:
        db.session.delete(channel_id)
        db.session.commit()
        return jsonify({'message': 'channel_id removed successfully'}),200
    else:
        return jsonify({'error':'channel_id not found'}),404
@yt_bp.route('/insights/view')
def insights_view():
    data = request.args
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
        metrics='views',#estimatedMinutesWatched,views,likes,subscribersGained,uniqueViewers
        dimensions='day',
        sort = 'day'
    ).execute()
    rows = response['rows']
    dates = [i[0] for i in rows]
    values = [i[1] for i in rows]
    metric_data = {'date':dates, 'values':values}
    return jsonify(metric_data)
@yt_bp.route('/insights/average_view_percentage')
def insights_average_view_percentage():
    data = request.args
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
        metrics='averageViewPercentage',#estimatedMinutesWatched,views,likes,subscribersGained,uniqueViewers
        dimensions='day',
        sort = 'day'
    ).execute()
    rows = response['rows']
    dates = [i[0] for i in rows]
    values = [i[1] for i in rows]
    metric_data = {'date':dates, 'values':values}
    return jsonify(metric_data)
@yt_bp.route('/insights/subscribe')
def insights_subscribe():
    data = request.args
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
        metrics='subscribersGained,subscribersLost',#estimatedMinutesWatched,views,likes,subscribersGained,uniqueViewers
        dimensions='day',
        sort = 'day'
    ).execute()
    # return jsonify(response)
    rows = response['rows']
    dates = [i[0] for i in rows]
    values1 = [i[1] for i in rows]
    values2 = [i[2] for i in rows]
    metric_data = {'date':dates, 'subscribersGained':values1, 'subscribers_lost':values2}
    return jsonify(metric_data)
@yt_bp.route('/insights/like')
def insights_like():
    data = request.args
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
        metrics='likes,dislikes,comments,shares',#estimatedMinutesWatched,views,likes,subscribersGained,uniqueViewers
        dimensions='day',
        sort = 'day'
    ).execute()
    rows = response['rows']
    dates = [i[0] for i in rows]
    values1 = [i[1] for i in rows]
    values2 = [i[2] for i in rows]
    values3 = [i[3] for i in rows]
    values4 = [i[4] for i in rows]
    metric_data = {'date':dates, 'likes':values1, 'dislikes':values2,'comments':values3,'shares':values4}
    return jsonify(metric_data)
@yt_bp.route('/insights/metric_option')
def insights_metrics():
    data = request.args
    channel_name = data.get('channel_name')
    metrics = data.get('metric','views')
    list_metric = [metric for metric in metrics.split(',')]
    # n_metrics = len(list_metric)
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
        metrics=metrics,#estimatedMinutesWatched,views,likes,subscribersGained,uniqueViewers
        dimensions='day',
        sort = 'day'
    ).execute()
    # list_metric = [metric for metric in list(metrics)]
    rows = response['rows']
    dates = [i[0] for i in rows]
    metric_data = {metric:[i[list_metric.index(metric) +1] for i in rows] for  metric in list_metric}
    metric_data['date'] = dates
    return jsonify(metric_data)
#######################top video by factors###########################
@yt_bp.route('/insights/top_video')
def insights_top_video():
    data = request.args
    channel_name = data.get('channel_name')
    metrics = str(data.get('metrics'))
    # list_metric = [metric for metric in metrics.split(',')]
    # n_metrics = len(list_metric)
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
    #f'channel=={channel_id}',
    # Fetch YouTube Analytics data
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics= metrics,
        dimensions='video',
        sort='-'+ metrics,
        maxResults=10,
        # filters='continent=142'
    ).execute()
    data = [{'video_id':i[0],metrics:i[1]} for i in response['rows']]
    video_ids = [i[0] for i in response['rows']]
    video_titles = get_video_titles(credentials, video_ids)
    for i in range(0,len(data)):
        data[i]['video_title'] = video_titles[data[i]['video_id']]
    # list_metric = [metric for metric in list(metrics)]
    # rows = response['rows']
    # dates = [i[0] for i in rows]
    # metric_data = {metric:[i[list_metric.index(metric) +1] for i in rows] for  metric in list_metric}
    # metric_data['date'] = dates
    return jsonify(data)
###############Additional charts###########################################################
@yt_bp.route('/insights/demension_metric_stats') 
def get_demension_metric_stats():
    data = request.args
    channel_name = data.get('channel_name')
    metrics = str(data.get('metrics'))
    dimensions = str(data.get('dimensions'))
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    refresh_token, channel_id = get_refresh_token(channel_name)
    temp_access_token = access_token_generate(refresh_token)
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics=metrics,
        dimensions=dimensions,
        filters='video==wdF1mYxG5eA',
        # sort='day,-views'
        # filters='province==US-CA'
        # filters='continent=142'
    ).execute()
    data =  response['rows']
    return jsonify(data)
@yt_bp.route('/insights/video_details')
def get_video_details():
    today = datetime.now().strftime('%Y-%m-%d')
    data = request.args
    video_id =  data.get('video_id')
    channel_name = data.get('channel_name')
    metrics = data.get('metrics')
    list_metrics = [
    #passed
    'views',
    'likes',
    'dislikes',
    'shares',
    'comments',
    'subscribersGained',
    'subscribersLost',
    'videosAddedToPlaylists',
    'videosRemovedFromPlaylists',
    'averageViewDuration',
    'averageViewPercentage',
    'annotationImpressions',
    'annotationClicks',
    'annotationCloses',
    'annotationClickThroughRate',
    'annotationCloseRate',
    'estimatedMinutesWatched',
    'cardClickRate',
    'cardTeaserClickRate',
    'cardImpressions',
    'cardTeaserImpressions',
    'cardClicks',
    'cardTeaserClicks',
    'averageViewPercentage',
    'averageViewDuration',
    
    #failed
    # 'estimatedRevenue',
    # 'adImpressions',
    # 'monetizedPlaybacks',
    # 'viewerPercentage'

    #testing
    '' 
    
]#data.get('metrics')  # specify the metrics you want
    metric = ','.join(list_metrics)
    dimensions = str(data.get('dimensions'))
    start_date = data.get('start_date',today)
    end_date = data.get('end_date',today)
    refresh_token, channel_id = get_refresh_token(channel_name)
    temp_access_token = access_token_generate(refresh_token)
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics=metrics,
        dimensions= dimensions,
        filters=f'video=={video_id}',
    ).execute()
    data =  response['rows']
    return jsonify(data)
#get distribution of watcher along the length of video
#performance of a video compare with other video at the same lenght
@yt_bp.route('/insights/elapsed_video_time_ratio')
def get_elapsed_video_time_ratio():
    today = datetime.now().strftime('%Y-%m-%d')
    data = request.args
    video_id =  data.get('video_id')
    channel_name = data.get('channel_name')
    dimensions = str(data.get('dimensions'))
    start_date = data.get('start_date',today)
    end_date = data.get('end_date',today)
    refresh_token, channel_id = get_refresh_token(channel_name)
    temp_access_token = access_token_generate(refresh_token)
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics='audienceWatchRatio,relativeRetentionPerformance',
        dimensions= dimensions,
        filters=f'video=={video_id}',
    ).execute()
    data =  response['rows']
    return jsonify(response)
###########################################################################################
###insert video to video table 
@yt_bp.route('/insights/channel_video_list')
def channel_video_list():
    data = request.args
    page = int(data.get('page',1))
    per_page = int(data.get('per_page',10))
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    channel_name = data.get('channel_name')
    # metrics = str(data.get('metrics'))
    refresh_token, channel_id = get_refresh_token(channel_name)
    temp_access_token = access_token_generate(refresh_token)
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    # API Key and Channel Details
    # Fetch all videos
    videos = get_all_videos(credentials, channel_id)
    for video in videos:
        if YoutubeVideoData.query.filter(YoutubeVideoData.video_id == video['video_id']).first():
            continue
        new_video = YoutubeVideoData(
            video_id = video['video_id'],
            video_title = video['video_title'],
            video_description = video['video_description'],
            published_at = video['published_at'],
            thumbnail_url = video['thumbnail_url'],
            channel_name = video['channel_name'],
            channel_id = video['channel_id'],
            playlist_id = video['playlist_id'],
        )
        db.session.add(new_video)
        db.session.commit()
        
    paginated_data = videos[start_index:end_index]

    # return jsonify(videos)
    return jsonify({'items':paginated_data,'page':page,'per_page':per_page, 'total_items':len(videos)})
############################################################################
##########Sentiment Analysis################################################
@yt_bp.route('/insights/video_analysis')
def video_analysis():
    data = request.args
    video_id =  data.get('video_id')
    # channel_name = data.get('channel_name')
    # Get the credentials from session
    
    # refresh_token, _ = get_refresh_token(channel_name)
    # temp_access_token = access_token_generate(refresh_token)
    # credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    developerKey = 'AIzaSyDnlnky7konGevRlfLfXQN50K3MlNUbE3c'
    comments = get_video_comments(developerKey = developerKey,video_id= video_id)
    offensives = 0
    spams =  0
    positives = 0
    comment_list = []
    for comment in comments:
        first_layer_comment = comment_classification(comment['comment'])
        comment_list.append(first_layer_comment)
        for reply in comment['replies']:
            reply_content = comment_classification(reply)
            comment_list.append(reply_content)
    for i in comment_list:
        if i['is_offensive'] == True:
            positives +=1
        if i['is_spam'] == True:
            spam +=1
        if i['sentiment'] == 'positive':
            positives +=1
    percent_offensives = offensives/len(comment_list) if len(comment_list) > 0 else 0
    percent_spams = spams/len(comment_list) if len(comment_list) > 0 else 0
    percent_positives = positives/len(comment_list) if len(comment_list) > 0 else 0
    data = {
        'content':comment_list,
        'analysis': {
            'offensive': {
                'is_offensive':100*percent_offensives
            },
            'spam': {
                'is_spam': 100*percent_spams
            },
            'sentiment':{
                'positive':100*percent_positives
            }
        }
    }
    return jsonify(data),200

####Get video from database
@yt_bp.route('/insights/get_channel_video_list')
def get_channel_video_list():
    data = request.args
    channel_name = data.get('channel_name')
    page = int(data.get('page',1))
    per_page = int(data.get('per_page',10))
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    results = db.session.query(
        YoutubeVideoData.video_id.label('video_id'),
        YoutubeVideoData.video_title.label('video_title'),
        YoutubeVideoData.video_description.label('video_description'),
        YoutubeVideoData.published_at.label('published_at'),
        YoutubeVideoData.thumbnail_url.label('thumbnail_url'),
        YoutubeVideoData.channel_name.label('channel_name'),
        YoutubeVideoData.channel_id.label('channel_id'),
        YoutubeVideoData.playlist_id.label('playlist_id'),
    ).filter(
        YoutubeVideoData.channel_name ==channel_name 
    ).all()
    data = [{
        'video_id': result.video_id,
        'video_title': result.video_title,
        'video_description': result.video_description,
        'published_at': result.published_at,
        'thumbnail_url': result.thumbnail_url,
        'channel_name': result.channel_name,
        'channel_id': result.channel_id,
        'playlist_id': result.playlist_id
    } for result in results]
    paginated_data = data[start_index:end_index]

    # return jsonify(videos)
    return jsonify({'items':paginated_data,'page':page,'per_page':per_page, 'total_items':len(data)})

################################################################################


###################################################################
@yt_bp.route("insights/channel_stat", methods = ['POST','GET'])
def get_channel_stat():
    data = request.args
    channel_name = data.get('channel_name')
    refresh_token, channel_id = get_refresh_token(channel_name)
    # temp_access_token = access_token_generate(refresh_token)
    credentials = Credentials(
        None,  # No initial access token, it will be obtained via the refresh token.
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret
    )

    # credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    # user__id = session['user_id']
    #get channel id
    youtube = build('youtube', 'v3', credentials=credentials)
    query = youtube.channels().list(
        part='id,snippet,contentDetails,statistics',
        id = channel_id
    )
    response = query.execute()
    return jsonify({'hahha':response})
@yt_bp.route('/test')
def test(): 
    # end_date = datetime.date.today().isoformat()
    return {'date':session['username']}
#SELECT * FROM `db_gg_channel` as c INNER JOIN `db_gg_user` u ON c.owner_id = u.user_id WHERE channel_name = "Shang Uchiha";
    # return end_date
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
# ya29.a0AXooCgu5g3bBX0fOhiVv_R-836FVvy8njpTEn18aY-Uwyx7O0OR5nDFFRXAGQHamtJLfw_H0UyL8-6e-OsDtHB_7kqVJqjE3iO1CCj80L4ZHF-h-Xx8HSbW31LWXH8Rrb3Lv-qBaW8EgcLtlNYbhCZd1OveU-wjd9Y5DaCgYKAdYSAQ8SFQHGX2MiB5L9i0KKjRHydr36UGC_0w0171
# ya29.a0AXooCgtGYLvbTh7W_pcpa56YauiqfZ4S1tgsIjqWXCiVO0J8vWc32wdX4p6ClxYnF6hMydQR0fgqi8Aza09sfrNMYcc_bR_6vBAYNxeOujxO8QxlebvIrHzRViVDIsO-LX--Ko_gDeAU72j3v9m7ZA0Oer01-Lih3IODaCgYKAWgSAQ8SFQHGX2MiMOA7-mM0sMGlZpfzxAYjJg0171