from flask import Flask, jsonify, request, session, make_response,redirect, url_for,Blueprint
yt_bp = Blueprint('yt_bp', __name__, url_prefix='/youtube')
from flask import Flask, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from model.db_schema import app, db, User, GoogleAccount, YoutubeChannel,YoutubeData, FacebookAccount,YoutubeVideoData, FacebookPage
import datetime
from datetime import datetime,timedelta
import time
import json
import os
import requests
import pymysql
import os
import re
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',  # To access YouTube channel data
    'https://www.googleapis.com/auth/userinfo.email',    # To access the user's email address
    'https://www.googleapis.com/auth/userinfo.profile' ,  # To access the user's profile information, including ID
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]
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
def get_all_videos(credentials, channel_id):
    # result = db.session.query()
    youtube = build('youtube', 'v3', credentials=credentials)

    # Fetch the channel's details to get the uploads playlist ID
    channel_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()
    uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    # List all videos in the uploads playlist
    videos = []
    next_page_token = None
    while True:
        playlist_items_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=10,  # Max allowed by API
            pageToken=next_page_token
        ).execute()

        videos += [{
            'video_id': item['snippet']['resourceId']['videoId'],
            'video_title': item['snippet']['title'],
            'video_description': item['snippet']['description'],
            'published_at': datetime.fromisoformat(item['snippet']['publishedAt']).strftime("%Y-%m-%d %H:%M:%S"),
            'thumbnail_url': item['snippet']['thumbnails']['default']['url'],
            'channel_name': item['snippet']['channelTitle'],
            'channel_id': channel_id,
            'playlist_id': item['snippet']['playlistId']
        } for item in playlist_items_response['items']]
        next_page_token = playlist_items_response.get('nextPageToken')
        if not next_page_token:
            break

    return videos
def get_video_comments(developerKey, video_id):
    youtube = build('youtube', 'v3', developerKey= developerKey)
    comments = []
    next_page_token = None
    while True:
        video_resonse = youtube.commentThreads().list(
            part="snippet,replies",
            maxResults=20,
            videoId=video_id,
            pageToken=next_page_token
        ).execute()
        comments += [{
            'comment': item['snippet']['topLevelComment']['snippet']['textDisplay'],
            'replies': [i['snippet']['textDisplay'] for i in item['replies']['comments']] if 'replies' in item else [],
        } for item in video_resonse['items']]
        next_page_token = video_resonse.get('nextPageToken')
        if not next_page_token:
            break
    return comments
def sentiment_classification(text):
    if len(text) >= 0:
        return 'Negative'
    else:
        return 'Positive'
def comment_classification(text):
    is_offensive = False
    is_spam = False
    # Define a list of Vietnamese bad words
    bad_words = ['buồi','buoi','dau buoi','daubuoi','caidaubuoi','nhucaidaubuoi','dau boi','bòi','dauboi','caidauboi','đầu bòy','đầu bùi','dau boy','dauboy','caidauboy','b`','cặc','cak','kak','kac','cac','concak','nungcak','bucak','caiconcac','caiconcak','cu','cặk','cak','dái','giái','zái','kiu','cứt','cuccut','cutcut','cứk','cuk','cười ỉa','cười ẻ','đéo','đếch','đếk','dek','đết','đệt','đách','dech',"đ'",'deo','d','đel','đél','del','dell ngửi','dell ngui','dell chịu','dell chiu','dell hiểu','dell hieu','dellhieukieugi','dell nói','dell noi','dellnoinhieu','dell biết','dell biet','dell nghe','dell ăn','dell an','dell được','dell duoc','dell làm','dell lam','dell đi','dell di','dell chạy','dell chay','deohieukieugi','địt','đm','dm','đmm','dmm','đmmm','dmmm','đmmmm','dmmmm','đmmmmm','dmmmmm','đcm','dcm','đcmm','dcmm','đcmmm','dcmmm','đcmmmm','dcmmmm','đệch','đệt','dit','dis','diz','đjt','djt','địt mẹ','địt mịe','địt má','địt mía','địt ba','địt bà','địt cha','địt con','địt bố','địt cụ','dis me','disme','dismje','dismia','dis mia','dis mie','đis mịa','đis mịe','ditmemayconcho','ditmemay','ditmethangoccho','ditmeconcho','dmconcho','dmcs','ditmecondi','ditmecondicho','đụ','đụ mẹ','đụ mịa','đụ mịe','đụ má','đụ cha','đụ bà','đú cha','đú con mẹ','đú má','đú mẹ','đù cha','đù má','đù mẹ','đù mịe','đù mịa','đủ cha','đủ má','đủ mẹ','đủ mé','đủ mía','đủ mịa','đủ mịe','đủ mie','đủ mia','đìu','đờ mờ','đê mờ','đờ ma ma','đờ mama','đê mama','đề mama','đê ma ma','đề ma ma','dou','doma','duoma','dou má','duo má','dou ma','đou má','đìu má','á đù','á đìu','đậu mẹ','đậu má','đĩ','di~','đuỹ','điếm','cđĩ','cdi~','đilol','điloz','đilon','diloz','dilol','dilon','condi','condi~','dime','di me','dimemay','condime','condimay','condimemay','con di cho','con di cho','condicho','bitch','biz','bít chi','con bích','con bic','con bíc','con bít','phò','4`','lồn','l`','loz','lìn','nulo','ml','matlon','cailon','matlol','matloz','thml','thangmatlon','thangml','đỗn lì','tml','thml','diml','dml','hãm','xàm lol','xam lol','xạo lol','xao lol','con lol','ăn lol','an lol','mát lol','mat lol','cái lol','cai lol','lòi lol','loi lol','ham lol','củ lol','cu lol','ngu lol','tuổi lol','tuoi lol','mõm lol','mồm lol','mom lol','như lol','nhu lol','nứng lol','nung lol','nug lol','nuglol','rảnh lol','ranh lol','đách lol','dach lol','mu lol','banh lol','tét lol','tet lol','vạch lol','vach lol','cào lol','cao lol','tung lol','mặt lol','mát lol','mat lol','xàm lon','xam lon','xạo lon','xao lon','con lon','ăn lon','an lon','mát lon','mat lon','cái lon','cai lon','lòi lon','loi lon','ham lon','củ lon','cu lon','ngu lon','tuổi lon','tuoi lon','mõm lon','mồm lon','mom lon','như lon','nhu lon','nứng lon','nung lon','nug lon','nuglon','rảnh lon','ranh lon','đách lon','dach lon','mu lon','banh lon','tét lon','tet lon','vạch lon','vach lon','cào lon','cao lon','tung lon','mặt lon','mát lon','mat lon','cái lờ','cl','clgt','cờ lờ gờ tờ','cái lề gì thốn','đốn cửa lòng','sml','sapmatlol','sapmatlon','sapmatloz','sấp mặt','sap mat','vlon','vloz','vlol','vailon','vai lon','vai lol','vailol','nốn lừng','vcl','vl','vleu','chịch','chich','vãi','v~','đụ','nứng','nug','đút đít','chổng mông','banh háng','xéo háng','xhct','xephinh','la liếm','đổ vỏ','xoạc','xoac','chich choac','húp sò','fuck','fck','đụ','bỏ bú','buscu','ngu','óc chó','occho','lao cho','láo chó','bố láo','chó má','cờ hó','sảng','thằng chó','thang cho','thang cho','chó điên','thằng điên','thang dien','đồ điên','sủa bậy','sủa tiếp','sủa đi','sủa càn','mẹ bà','mẹ cha mày','me cha may','mẹ cha anh','mẹ cha nhà anh','mẹ cha nhà mày','me cha nha may','mả cha mày','mả cha nhà mày','ma cha may','ma cha nha may','mả mẹ','mả cha','kệ mẹ','kệ mịe','kệ mịa','kệ mje','kệ mja','ke me','ke mie','ke mia','ke mja','ke mje','bỏ mẹ','bỏ mịa','bỏ mịe','bỏ mja','bỏ mje','bo me','bo mia','bo mie','bo mje','bo mja','chetme','chet me','chết mẹ','chết mịa','chết mja','chết mịe','chết mie','chet mia','chet mie','chet mja','chet mje','thấy mẹ','thấy mịe','thấy mịa','thay me','thay mie','thay mia','tổ cha','bà cha mày','cmn','cmnl','tiên sư nhà mày','tiên sư bố','tổ sư']  
    # Define a regular expression pattern to match Vietnamese spam URLs
    url_pattern = r'(https?://)?(www\.)?([a-zA-Z0-9]+(-[a-zA-Z0-9]+)*\.)+[a-zA-Z]{2,}(/(\S+)*)?'
    if re.search(url_pattern, text):
       is_spam = True
    else:
       is_spam = False
    # Remove bad words
    is_offensive = any(word in text.lower() for word in bad_words)
    sentiment_class = sentiment_classification(text)
    result = {'content':text,'is_spam': is_spam,'is_offensive':is_offensive,'sentiment': sentiment_class}
    return  result
def load_client_credentials(json_filepath):
    """Load client_id and client_secret from a credentials.json file."""
    with open(json_filepath, 'r') as file:
        data = json.load(file)
    
    client_id = data['web']['client_id']
    client_secret = data['web']['client_secret']
    token_uri = data['web']['token_uri']
    return client_id, client_secret, token_uri
#####################################################################
##write some functions to extract parameters from specigfic channel
##endpoints create here only for testing purpose
######################################################################
#get refresh token
def get_refresh_token(channel_name):
    results = db.session.query(
        YoutubeData.channel_id, 
        YoutubeData.refresh_token
    ).filter(
        YoutubeData.channel_name == channel_name
    ).all()
    if not results:
        return jsonify({'message':'no record found'}),404
    data = [{'channel_id': result.channel_id, 'refresh_token':result.refresh_token} for result in results]
    channel_id = data[0]['channel_id']
    refresh_token = data[0]['refresh_token']

    return refresh_token,channel_id
# refresh_token,channel_id = get_refresh_token("Shang Uchiha")
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
# temp_access_token = access_token_generate(refresh_token)
#Create Credentials object
def credentials_generate(access_token, refresh_token,token_uri,client_id,client_secret):
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES)
def get_video_titles(credentials, video_ids):
    youtube = build('youtube', 'v3', credentials=credentials)
    video_response = youtube.videos().list(
        part='snippet',
        id=','.join(video_ids)  # Pass video IDs as a comma-separated string
    ).execute()

    # Create a dictionary of video IDs to titles
    video_titles = {item['id']: item['snippet']['title'] for item in video_response.get('items', [])}
    return video_titles
##########################Cron job#########################################
def get_5goal_news_video_stats(video_id,n_days):
    today = datetime.now()#.strftime('%Y-%m-%d')
    # today_str = today.strftime('%Y-%m-%d')
    data = request.args
    # video_id =  data.get('video_id')
    channel_name = '5GOAL NEWS'
    # metrics = data.get('metrics')
    list_metrics = [
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
    'averageViewDuration']
    metrics = ','.join(list_metrics)
    n_days_befor =  today - timedelta(days=n_days)
    n_days_befor_str =  n_days_befor.strftime('%Y-%m-%d')
    # dimensions = 'day', #str(data.get('dimensions'))
    start_date =n_days_befor_str #data.get('start_date',today)
    end_date = n_days_befor_str#data.get('end_date',today)
    refresh_token, channel_id = get_refresh_token(channel_name)
    temp_access_token = access_token_generate(refresh_token)
    credentials = credentials_generate(temp_access_token, refresh_token,token_uri,client_id,client_secret)
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_id}',
        startDate=start_date,
        endDate=end_date,
        metrics=metrics,
        dimensions= 'day',
        filters=f'video=={video_id}',
    ).execute()
    data =  response['rows']
    return data,n_days_befor_str
def get_all_video_ids_5goalnews():
    video_ids = []
    videos = YoutubeVideoData.query.filter(
        YoutubeVideoData.channel_name == '5GOAL NEWS'
    ).all()
    for video in videos:
        video_ids.append(video.video_id)
    return video_ids
###############################
def get_all_name():
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
    
    return user_data
###########################################################################

CLIENT_SECRETS_FILE = "cred3.json"
client_id, client_secret, token_uri = load_client_credentials(CLIENT_SECRETS_FILE)
