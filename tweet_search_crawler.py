#
# tweet seach crawler 
#

#
# twitter search API
# https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets.html
# https://developer.twitter.com/en/docs/tweets/search/guides/standard-operators
#

#%%
import json
from requests_oauthlib import OAuth1Session
import sqlite3
from contextlib import closing
import sys, json, time, calendar
import datetime
import argparse
from distutils.util import strtobool

CONSUMER_KEY        = 'XXXXXXXXXX'
CONSUMER_SECRET_KEY = 'XXXXXXXXXX'
ACCESS_TOKEN        = 'XXXXXXXXXX'
ACCESS_TOKEN_SECRET = 'XXXXXXXXXX'

#
# Command Line Parameter
#
# example:
# $ python tweet_search_crowler.py --query 'yahooooo' --dbpath 'yahooooo.db'
#
parser = argparse.ArgumentParser()
parser.add_argument("--query", required = True, help="Search Query", type=str)
parser.add_argument("--dbpath", required = True, help="SQLite Database Path", type=str)
parser.add_argument("--safe-mode", help="[optional] Stop if registered", type=strtobool, default='True')
parser.add_argument("--debug-mode", help="[optional] Do not write database and recursion", type=strtobool, default='False')
parser.add_argument("--last-tweet-id", help="[optional] Request max_id parameter", type=int, default=0)
args = parser.parse_args()
print("Command Line Parameter :: ", args, sep="\n")
query = args.query
dbpath = args.dbpath
safe_mode = bool(args.safe_mode)
debug_mode = bool(args.debug_mode)
last_tweet_id = args.last_tweet_id

#
# twitter API Request
#
twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
url = "https://api.twitter.com/1.1/search/tweets.json"
q = query + ' -filter:retweets'
params = {
    'q' : q,
    'count' : 100,
    'lang' : 'ja',
    'locale' : 'ja',
    'result_type' : 'mixed',
    #'until' : '2019-04-01',
    }
print("Request Parameter :: ", params, sep="\n")

#
# Database session 
#
connect = sqlite3.connect(dbpath)
cursor = connect.cursor()
if not debug_mode:
    create_sql = "CREATE TABLE IF NOT EXISTS tweet( tweet_id integer primary key, user_id integer, user_screen_name text, user_name text, user_description text, search_query text, tweet_text text, created_at_jpdate numeric, created_at_utime numeric)"
    cursor.execute(create_sql)
    connect.commit()

#
# crawl twitter
#
while(True):
    if last_tweet_id:
        params['max_id']  = last_tweet_id - 1

    print("---------- %s ----------" % datetime.datetime.now())
    print("Request search API :: last_tweet_id=%s" % last_tweet_id)
    req = twitter.get(url, params = params)

    if req.status_code != 200:
        # Limit: 180 requests in 15 minutes requests
        print("ERROR: %d" % req.status_code)
        sleep_sec = 5 * 60
        print('Sleeping %d sec ...' % sleep_sec)
        time.sleep(sleep_sec)
        continue

    search_timeline = json.loads(req.text)

    if search_timeline['statuses'] == []:
        print("statuses is empty.")
        break

    no_success = True
    for tweet in search_timeline['statuses']:
        #print("tweet row data :: ", tweet)
        last_tweet_id = tweet['id']
        time_utc = time.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
        unix_time = calendar.timegm(time_utc)
        time_local = time.localtime(unix_time)
        japan_time = time.strftime("%Y%m%d%H%M%S", time_local)
        bind = [
            tweet['id_str'],
            tweet['user']['id_str'],
            tweet['user']['screen_name'],
            tweet['user']['name'],
            tweet['user']['description'],
            query,
            tweet['text'],
            japan_time,
            unix_time,
         ]  

        if debug_mode:
            print("tweet data :: ", bind, sep="\n")
            continue

        try:
            cursor.execute("insert into tweet (tweet_id, user_id, user_screen_name, user_name, user_description, search_query, tweet_text, created_at_jpdate, created_at_utime) values (?,?,?,?,?,?,?,?,?)", bind)
            connect.commit()
            no_success = False
        except Exception as e:
            print("Exception _query=%s, tweet_id=%s" % (e, tweet['id_str']))

    if no_success and safe_mode:
        print("already registered.")
        break

    time.sleep(3)

connect.close()
print("Finish...")
