from flask import Flask, redirect, request, session, url_for,jsonify
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import os

app = Flask(__name__)
app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679'  # Replace with a strong secret key
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for testing on localhost without HTTPS

# Google OAuth 2.0 Setup
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
session.clear()
CLIENT_SECRETS_FILE = 'cred3.json'
channel_ids = []
@app.route('/')
def index():
    if 'credentials' not in session:
        return '<a href="/authorize">Authorize Access to YouTube</a>'
    # User is authenticated, proceed with API calls
    else:
        return redirect(url_for("list_channels"))
    # return '<a href="/authorize">Authorize Access to YouTube</a>'

@app.route('/authorize')
def authorize():
    flow = Flow.from_client_secrets_file(
        client_secrets_file=CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True))
    #Flow generate authorization url and state to save to session
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent')
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state,
        redirect_uri=url_for('oauth2callback', _external=True))
    
    # Exchange client_id for refresh_token and access token
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session['credentials'] = {
        #access token
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    print(session['credentials'])
    return redirect(url_for('list_channels'))

def session_to_credentials(session_credentials):
    from google.oauth2.credentials import Credentials
    
    return Credentials(
        token=session_credentials['token'],
        refresh_token=session_credentials['refresh_token'],
        token_uri=session_credentials['token_uri'],
        client_id=session_credentials['client_id'],
        client_secret=session_credentials['client_secret'],
        scopes=session_credentials['scopes'])
@app.route('/list_channels')
def list_channels():
    if 'credentials' not in session:
        return redirect('authorize')
    
    credentials = session_to_credentials(session['credentials'])
    youtube = build('youtube', 'v3', credentials=credentials)

    request = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        mine=True
    )
    response = request.execute()

    channels = []
    for item in response.get('items', []):
        channels.append({
            'name': item['snippet']['title'],
            'id': item['id']
        })
        if item['id'] not in channel_ids:
            channel_ids.append(item['id'])
    # return jsonify(channels)
        return channel_ids
#Get metrics of a chanel
@app.route('/channel_statistics')
def channel_statistics():
    if 'credentials' not in session:
        return redirect('authorize')

    # Reconstruct credentials from the session
    credentials = Credentials(**session['credentials'])

    # Build the YouTube Analytics service object
    youtubeAnalytics = build('youtubeAnalytics', 'v2', credentials=credentials)

    # Define the date range for the last 30 days
    end_date = (datetime.date.today() +  datetime.timedelta(days=0)).isoformat()

    start_date = (datetime.date.today() - datetime.timedelta(days=100)).isoformat()

    # Fetch YouTube Analytics data
    # ID  = UCek4r6Ttj5nMmi5zt58jZng
    response = youtubeAnalytics.reports().query(
        ids=f'channel=={channel_ids[0]}',
        startDate='2024-03-01',
        endDate='2024-03-30',
        metrics='views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,impressions,clicks,ctr',
        dimensions='day',
        sort = 'day'
    ).execute()
    if response.get("rows"):
        for row in response["rows"]:
            print(row)
    else:
        print("No data returned. Check your query parameters.")
    # Update the session with the new tokens
    session['credentials'] = credentials_to_dict(credentials)

    # return jsonify(response)
    return response
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
if __name__ == '__main__':
    app.run('localhost', 5000, debug=False)