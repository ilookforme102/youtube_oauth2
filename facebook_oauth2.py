from flask import Flask, request, redirect, session,jsonify,session
import requests
from datetime import datetime
import time
app = Flask(__name__)
app.secret_key = 'f33924fea4dd7123a0daa9d2a7213679' #auto generate
#IDs for the app
#######################################################################
##############LINK TO API DOC##########################################
#API documentation https://developers.facebook.com/docs/graph-api/reference/insights/#page-reactions
#Token Debug: https://developers.facebook.com/tools/debug/accesstoken/
ACCESS_TOKEN = 'EAAUZBgUiZAG9oBO6t8ZCO9LgSVgc0gMepoUBLqZAvlZBSvrqZAfjiZBQ6e5uUepOlzZASNT8cTytIEdwrxjzDajMc0mEwKSG0uItFtKwO6ZClTFZBxTTJxn7sgsstjFPL98kxRZAITdJ9JtlqxCE8ttahRBAFGmR9NZAolyZCt9Wc1Rbgu9Nd0kl0icRs4bsXTDZB7HF2CfPcierwdgJX7tJa7RbYZD'
CLIENT_SECRET = 'cb10b0592db22018171a652375a7513a' #AKA App secret
CLIENT_TOKEN = '26f7416272ab27f379c4d75a6ca77dd1'
CLIENT_ID = '1476099873250266' #AKA app id
REDIRECT_URI = 'http://localhost:5000/callback'
@app.route('/login')
def home_page():
    # https://www.facebook.com/dialog/oauth?client_id=1476099873250266&redirect_uri=http://localhost:5000/callback&scope=pages_show_list,pages_read_engagement,read_insights&response_type=code
    return redirect(f'https://www.facebook.com/dialog/oauth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=pages_show_list,pages_read_engagement,read_insights&response_type=code')
@app.route('/')
def home():
    if 'logged_in' in session and session['logged_in']:
        # User is logged in, redirect to another URL
        return redirect('/data')
    else:
        # User is not logged in, redirect to login or show a landing page
        return redirect('/login')
@app.route('/callback')
def callback():
    # Facebook redirects back to your site with a code in the URL
    #http://localhost:5000/callback?code=AQALkZj3kvKBr7GO-KqEhOMoI7uZ1NQ_D55vtm461ip9zlBNvW90cSLIBsP1h6l-poyixWrAchLylE6sFPyameRwMCsRpmDbxgfu5saYrSbLC5FLSHvNr1ealab8i-6Mn5ITKHVlqHGbgZFQ_v_a36xm5GZ5rfG0EZHjNtoewXb_USkxnl87dbo0E_-N0j1ulTm9NkI49wKQUZXxb6d3VVCxye6GWMVT6wd4ZGhg0SL5_wYbqNY1C6FjiE-74j9xmXg4DmO54iAvhLsnVq_r4bODft4I3EgUsCgtNPuXPrAy3gx87bCANax5g9Us5NN8Hakt8qOa6vVcIXmpmnzg_ik1FHQJR5nIxKMs05zsLwM4fOxrNp74u28bL23Gr3CnX_Y#_=_
    code = request.args.get('code')
    if code:
        # Exchange code for an access token
        token_url = f'https://graph.facebook.com/v19.0/oauth/access_token?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&client_secret={CLIENT_SECRET}&code={code}'
        response = requests.get(token_url)
        user_access_token = response.json().get('access_token')

        # Use the access token to access the Facebook API
        #me_url = f'https://graph.facebook.com/v19.0/me?access_token={user_access_token}'
        me_url = f'https://graph.facebook.com/v19.0/me/accounts?access_token={user_access_token}'
        user_data = requests.get(me_url).json()
        session['logged_in'] = True
        session['code'] = code
        session['user_access_token'] = user_access_token
        # Do something with the user data, for example, display the user's name
        session['page_data'] = user_data['data'][0]
        return f'Hello, {session['page_data']}!'
    else:
        return 'Access denied or cancelled by user', 400
@app.route('/extend_token')
def extend_token():
    short_live_user_token = session['user_access_token']
    url = f'https://graph.facebook.com/v19.0/oauth/access_token'
    params = {
        'grant_type': 'fb_exchange_token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'fb_exchange_token': short_live_user_token
    }
    response = requests.get(url, params=params)
    long_live_user_token = response.json().get('access_token',[])
    session['long_live_user_token'] = long_live_user_token
    return long_live_user_token
@app.route('/test')
def test():
    url = f'https://graph.facebook.com/v19.0/me/accounts'
    params = {
        'access_token': session['long_live_user_token']
    }
    response = requests.get(url, params = params)
    page_long_live_token = response.json().get('data',[])[0].get('access_token')
    session['page_long_live_token'] = page_long_live_token
    return session.get('page_long_live_token')#page_long_live_token
@app.route('/data')
def data():
    return session.get('page_long_live_token')
@app.route('/page')
def page():
    page_id = session['page_data']['id']
    page_access_token = session['page_long_live_token']#session['page_data']['access_token']
    start_date_str = '14/03/2024'
    end_date_str = '14/04/2024'
    start_date_object = datetime.strptime(start_date_str, '%d/%m/%Y')
    start_date_object = datetime.strptime(end_date_str, '%d/%m/%Y')

    # Convert datetime object to UNIX timestamp
    start_date = int(time.mktime(start_date_object.timetuple()))
    end_date = int(time.mktime(start_date_object.timetuple()))
    metrics = 'page_impressions,page_post_engagements,page_views_total,page_fans'
    url = f'https://graph.facebook.com/v19.0/{page_id}/insights'
    params = {
        'pretty':0,
        'metric':metrics,
        'period':'day',
        'since': start_date,
        'until': end_date,
        'access_token':page_access_token
    }
    response = requests.get(url,params=params)
    insights_data = response.json()
    return insights_data
    # return page_access_token
    #https://www.facebook.com/v19.0/dialog/oauth?response_type=token&display=popup&client_id=1476099873250266&redirect_uri=https%3A%2F%2Fdevelopers.facebook.com%2Ftools%2Fexplorer%2Fcallback%3Fmethod%3DGET%26path%3Dme%252Faccounts%253Ffields%253Dpage_token%26version%3Dv19.0&auth_type=rerequest&scope=email%2Cpages_manage_cta%2Cpages_show_list%2Cads_read%2Cpages_messaging%2Cpages_read_engagement%2Cpages_manage_metadata%2Cpages_read_user_content%2Cpages_manage_ads%2Cpages_manage_posts%2Cpages_manage_engagement


@app.route('/get_page_engagements', methods=['POST'] )
def get_page_engagements():
    page_id = '265201166672768'#session['page_data']['id']
    page_access_token = session.get('page_long_live_token')
    data = request.json
    start_date_str = data.get('start_date') 
    end_date_str = data.get('end_date') 
    start_date_object = datetime.strptime(start_date_str, '%d/%m/%Y')
    start_date_object = datetime.strptime(end_date_str, '%d/%m/%Y')
    # Convert datetime object to UNIX timestamp
    start_date = int(time.mktime(start_date_object.timetuple()))
    end_date = int(time.mktime(start_date_object.timetuple()))
    metrics = 'page_impressions,page_post_engagements,page_views_total,page_fans'
    url = f'https://graph.facebook.com/v19.0/{page_id}/insights'
    params = {
        'pretty':0,
        'metric':metrics,
        'period':'day',
        'since': start_date,
        'until': end_date,
        'access_token':page_access_token
    }
    response = requests.get(url,params=params)
    insights_data = response.json()
    return page_access_token
if __name__ == '__main__':
    app.run('localhost', 5000,debug=True)