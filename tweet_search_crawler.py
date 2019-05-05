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
# $ python tweet_search_crawler.py --query 'yahooooo' --dbpath 'yahooooo.db'
#
parser = argparse.ArgumentParser()
parser.add_argument("--query", required = True, help="Search Query", type=str)
parser.add_argument("--dbpath", required = True, help="SQLite Database Path", type=str)
parser.add_argument("--max-id", help="[optional] Returns results with an ID less than or equal to the specified ID", type=int, default=0)
parser.add_argument("--until", help="[optional] Returns tweets created before the given date(YYYY-MM-DD)", type=str, default='')
parser.add_argument("--full-crawl", help="[optional] Crawl all Tweet", type=strtobool, default='False')
parser.add_argument("--debug-mode", help="[optional] Log only", type=strtobool, default='False')
args = parser.parse_args()
print("Command Line Parameter :: ", args, sep="\n")
query = args.query
dbpath = args.dbpath
max_id = args.max_id
until = args.until
full_crawl = bool(args.full_crawl)
debug_mode = bool(args.debug_mode)

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
    'until' : until,
    }
print("Request Parameter :: ", params, sep="\n")

#
# Database session 
#
connect = sqlite3.connect(dbpath)
cursor = connect.cursor()
if not debug_mode:
    create_sql = "CREATE TABLE IF NOT EXISTS tweet(tweet_id integer primary key, user_id integer, user_screen_name text, user_name text, user_description text, search_query text, tweet_text text, created_at_jpdate numeric, created_at_utime numeric)"
    cursor.execute(create_sql)
    connect.commit()

#
# crawl twitter
#
registered_cnt = 0
registered_limit = 3000
reqerror_cnt = 0
reqerror_limit = 10
while(True):
    if max_id:
        params['max_id']  = max_id

    print("---------- %s ----------" % datetime.datetime.now())
    print("Request search API :: params=%s" % params)
    req = twitter.get(url, params = params)

    if req.status_code != 200:
        # Limit: 180 requests in 15 minutes requests
        print("HTTP Status Error :: %d" % req.status_code)
        if req.status_code == 429:
            print('Limit error :: 180 calls every 15 minutes.')
            sleep_sec = 5 * 60
            print('Sleep %d sec ...' % sleep_sec)
            time.sleep(sleep_sec)
            continue
        else:
            if reqerror_cnt >= reqerror_limit:
                print('Stop because an error occurred.')
                break
            else:
                print('Sleep because an error occurred.')
                reqerror_cnt += 1
                time.sleep(10)
                continue

    reqerror_cnt = 0
    search_timeline = json.loads(req.text)

    if len(search_timeline['statuses']) <= 1:
        print("Statuses is empty.")
        break

    for tweet in search_timeline['statuses']:
        if max_id == tweet['id']:
            print("Skip max_id :: tweet_id=%s" % tweet['id_str'])
            continue

        #print("tweet row data :: ", tweet)
        max_id = tweet['id']
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
            print("Tweet data :: ", bind, sep="\n")
            continue

        try:
            cursor.execute("SELECT COUNT(*) AS count FROM tweet WHERE tweet_id = ?", [tweet['id_str']])
            result = cursor.fetchall()
            if result[0][0] > 0:
                print("Already inserted :: tweet_id=%s" % tweet['id_str'])
                registered_cnt += 1
                continue

            registered_cnt = 0
            cursor.execute("INSERT INTO tweet (tweet_id, user_id, user_screen_name, user_name, user_description, search_query, tweet_text, created_at_jpdate, created_at_utime) VALUES (?,?,?,?,?,?,?,?,?)", bind)
            connect.commit()
            print("Insert :: tweet_id=%s" % tweet['id_str'])
        except Exception as e:
            print("Exception :: tweet_id=%s, _query=%s" % (tweet['id_str'], e))

    if registered_cnt >= registered_limit and not full_crawl:
        print("Maybe the remaining tweets are registered.")
        break

    print("Last Tweet ID :: %s" % max_id)
    print("Continuous registered count :: %s" % registered_cnt)
    time.sleep(2)

connect.close()
print("Finish...")
