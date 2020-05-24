import twitter
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime, timezone
import pandas as pd
from gspread_pandas import Spread
import json

#Global Variables
banned_words = ['Twitter', 'robot']
TWITTER_LIST_ID = '1042268003302354949'
GOOGLE_SERVICE_CREDS_LOCATION = 'google_service_account.json'
TWITTER_CREDS_LOCATION = 'twitter_creds.json'
GOOGLE_SHEETS_ID = '1oY7URLTauSIBJKS9z7AKAPTHajyvy4GhTQ016PkB20M'

def find_banned_words(title_text, banned_words):
    dont_return_text = True
    for word in banned_words:
        if re.search(word, title_text):
            dont_return_text = False
    return dont_return_text

def get_page_title(url, banned_words):
    r = requests.get(url)
    if r.status_code == 200:
        html_doc = r.content
        soup = BeautifulSoup(html_doc)
        if soup.title:
            parse_title = find_banned_words(soup.title.text, banned_words)
            if parse_title:
                page_title = soup.title.text
    try:
        return page_title
    except:
        return None
    
def retrieve_link(tweet_str):
    title_search = re.search('https.*', tweet_str)
    if title_search:
        return title_search.group(0) 
    
def get_time_difference(created_at):
    difference_seconds = (datetime.now(timezone.utc) - datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')).seconds
    return difference_seconds

def pull_status(status):
    if status.retweeted_status:
        status = status.retweeted_status
    if status.quoted_status:
        status = status.quoted_status
    text = status.full_text
    retweet_count = status.retweet_count
    status_id = status.id
    created_at = status.created_at
    link = retrieve_link(text)
    if link:
        page_title = get_page_title(link, banned_words)
        if page_title:
            difference_seconds = get_time_difference(created_at)
            return [page_title, link, retweet_count, status_id, difference_seconds]

def main_function():
    with open('twitter_creds.json') as f:
        twitter_credentials = json.load(f)
    api = twitter.Api(consumer_key=twitter_credentials['CONSUMER_KEY'],
	                  consumer_secret=twitter_credentials['CONSUMER_SECRET'],
	                  access_token_key=twitter_credentials['ACCESS_TOKEN'],
	                  access_token_secret=twitter_credentials['ACCESS_TOKEN_SECRET'],
	                  tweet_mode='extended')
    relevant_members = api.GetListMembers(list_id=TWITTER_LIST_ID)
    master_list = []
    for user in relevant_members:
        recent_tweets = api.GetUserTimeline(user_id=user.id)
        for status in recent_tweets:
            result = None
            result = pull_status(status)
            if result:
                master_list.append(result)
    df = pd.DataFrame(master_list, columns=['title', 'link', 'retweets', 'tweet_id', 'seconds_since'])
    df = df.sort_values('retweets', ascending=False).reset_index(drop=True)
    with open(GOOGLE_SERVICE_CREDS_LOCATION) as f:
        service_account = json.load(f)
    spread = Spread(GOOGLE_SHEETS_ID, config=service_account)
    spread.df_to_sheet(df, index=False, sheet='news', start='A1')
    
if __name__ == "__main__":
    main_function()