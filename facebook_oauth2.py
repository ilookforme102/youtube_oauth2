from flask import Flask, request, redirect, session,jsonify,session,url_for
import requests
from datetime import datetime, timezone
import time
import pymysql
app = Flask(__name__)
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=91)
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
host='128.199.228.235'
user='sql_dabanhtructi'
password='FKb75AYJzFMJET8F'
database='sql_dabanhtructi'
port = 3306
#Get data from database sample
def get_data(sql):
    conn = pymysql.connect(
            host='128.199.228.235', 
            user='sql_dabanhtructi', 
            password='FKb75AYJzFMJET8F', 
            database='sql_dabanhtructi',
            #connect_timeout=30000,
            port = 3306)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except pymysql.OperationalError as e:
            if e.args[0] in (2006,2003, 2013):
                print("Lost connection, attempting to reconnect...")
                conn.ping(reconnect=True)
                cursor.execute(sql)
            else:
                print("An error occurred:", e)
                conn.rollback()
    except Exception as e:
        print(e)
        conn.rollback()

    # Fetch all the rows in a list of lists.
    rows = cursor.fetchall()
    return list(rows)
##########################################
#Check for validation
##If logged in redirect token validation
##Else go to login endpoint

@app.route('/')
def home():
    if 'logged_in' in session and session['logged_in']:
        # User is logged in, redirect to another URL
        return redirect('/token_validate')
    else:
        # User is not logged in, redirect to login or show a landing page
        return redirect('/login')
def convert_date(unix_timestamp):
    # Convert Unix timestamp to datetime object in UTC
    dt_object = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
    # Format datetime object as a string 'ddmmyy'
    date_string = dt_object.strftime('%d%m%y')
    return date_string
@app.route('/token_validate')
def token_validate():
    long_live_user_token = session['long_live_user_token']
    url = 'https://graph.facebook.com/v19.0/debug_token'
    params = {
        'input_token':long_live_user_token,
        'access_token':long_live_user_token
    }
    response = requests.get(url, params=params)    
    data_access_expires_at =  response.json().get('data',[])["data_access_expires_at"]
    date_string  =convert_date(data_access_expires_at)
    return {"exprided_date":date_string}
   
@app.route('/login')
def home_page():
    # https://www.facebook.com/dialog/oauth?client_id=1476099873250266&redirect_uri=http://localhost:5000/callback&scope=pages_show_list,pages_read_engagement,read_insights&response_type=code
    return redirect(f'https://www.facebook.com/dialog/oauth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=pages_show_list,pages_read_engagement,read_insights&response_type=code')

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
        
        session['logged_in'] = True
        session['code'] = code
        session['user_access_token'] = user_access_token
        # Do something with the user data, for example, display the user's name
        return redirect(url_for("extend_token"))
    else:
        return 'Access denied or cancelled by user', 400
###################################################################
############Get long live user token and long live page token######
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
    me_url = f'https://graph.facebook.com/v19.0/me/accounts?access_token={long_live_user_token}'
    user_data = requests.get(me_url).json()
    session['page_data'] = user_data['data'][0]
    return redirect(url_for("get_user_info"))
#######################################################
############Get user name and id#######################
@app.route('/get_user_info')
def get_user_info():
    user_access_token = session['long_live_user_token']
    url = f'https://graph.facebook.com/v19.0/me'
    params = {
        'access_token': user_access_token
    }
    response = requests.get(url, params = params)
    user_name = response.json().get('name',[])
    user_id = response.json().get('id',[])
    session['user_name'] = user_name
    session['user_id']= user_id
    return redirect(url_for("save_user_info"))
@app.route('/save_user_info')
def save_user_info():
    conn = pymysql.connect(host=host,user=user, password=password, database=database,port=port)
    try:
    # Create a cursor object
        with conn.cursor() as cursor:
            # SQL INSERT statement
            sql = "INSERT INTO `db_fb_user` (`user_id`, `user_name`, `short_live_user_token`, `long_live_user_token`) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE `user_id` = VALUES(`user_id`),`user_name` = VALUES(`user_name`),`short_live_user_token` = VALUES(`short_live_user_token`),`long_live_user_token` = VALUES(`long_live_user_token`) "
            
            # Values to insert
            values = (session['user_id'], session['user_name'], session['user_access_token'],session['long_live_user_token'])
            
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
    return redirect(url_for("done"))
@app.route('/done')
def done():
    return "your data is fucking stolen"

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
    return session.get('page_data')

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
@app.route('/page_fetch')
def page_fetch():
    sql = "SELECT * FROM `db_fb_page` LIMIT 10;"
    rows = get_data(sql)
    return rows
@app.route('/get_page_engagements', methods=['POST'] )
def get_page_engagements():
    page_id = '265201166672768'#session['page_data']['id']
    page_access_token = session.get('page_long_live_token',[])
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