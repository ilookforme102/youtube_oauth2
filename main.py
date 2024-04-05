from flask import Flask, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime
import os

app = Flask(__name__)
app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679'  # Needed for session tracking

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
@app.route('/')
def index():
    # Check if the user is authenticated
    if 'credentials' not in session:
        return '<a href="/authorize">Authorize Access to YouTube</a>'
    # User is authenticated, proceed with API calls
    return redirect("/fetch_youtube_metrics")

@app.route('/authorize')
def authorize():
    # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow steps
    #The flow object is used to generate an authorization URL to which the user will be 
    #redirected. This URL directs the user to Google's OAuth 2.0 server, 
    #where they can authorize your application to access their Google data 
    #according to the scopes you've requested.
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        #Declare the url to redirect to after authorize my application to access their Google data
        redirect_uri=url_for('oauth2callback', _external=True))
    # authorization_url is url to redirect to from /authorize
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true', prompt = 'consent')

    # Store the state in the session so you can verify the callback
    session['state'] = state
    # At this url, server will redicrect user to Google's OAuth 2.0 server
    return redirect(authorization_url)
 
@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback to verify the authorization server response
    state = session['state']

    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state,
        redirect_uri=url_for('oauth2callback', _external=True))

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    # Print out the refresh token
    print(f"Refresh Token: {credentials.refresh_token}")

    return 'Authorization complete. Check the console for the refresh token.'
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
    #Get user id and email
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
        if item['id'] not in channel_ids:
            channel_ids.append(item['id'])
    # return jsonify(channels)
    session['channel_data'] = channels
    return session['channel_data']
@app.route('/test')
def test():
    return session['credentials']
@app.route('/fetch_youtube_metrics')
def fetch_youtube_metrics():
    channel_id = session['channel_data'][0]['id']
    if 'credentials' not in session:
        return redirect('authorize')

    # Reconstruct credentials from the session
    credentials = Credentials(**session['credentials'])

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
    app.run('localhost', 5000, debug=True)
