import twitter
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime, timezone, timedelta
import pandas as pd
from gspread_pandas import Spread
import json

class TwitterPull:
    def __init__(self):
        self.banned_words = ['Twitter', 'robot', 'YouTube', 'Instagram']
        self.TWITTER_LIST_ID = '1042268003302354949'
        self.GOOGLE_SERVICE_CREDS_LOCATION = 'google_service_account.json'
        self.TWITTER_CREDS_LOCATION = 'twitter_creds.json'
        self.GOOGLE_SHEETS_ID = '1oY7URLTauSIBJKS9z7AKAPTHajyvy4GhTQ016PkB20M'
        self.time_limit = 172800 # 48 hours
        self.sheet_name = 'news'

    def find_banned_words(self, title_text):
        dont_return_text = True
        for word in self.banned_words:
            if re.search(word, title_text):
                dont_return_text = False
        return dont_return_text

    def get_page_title(self, url):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                html_doc = r.content
                soup = BeautifulSoup(html_doc)
                if soup.title:
                    parse_title = self.find_banned_words(soup.title.text)
                    if parse_title:
                        [s.decompose() for s in soup("script")]  # remove <script> elements
                        body_text = soup.body.get_text()
                        language = detect(body_text)
                        if language == 'en':
                            page_title = soup.title.text
        except:
            pass
        try:
            return page_title
        except:
            return None
    
    def get_time_difference(self, created_at):
        difference_seconds = (datetime.now(timezone.utc) - datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')).total_seconds()
        return difference_seconds

    def pull_status(self, status):
        screen_name = status.user.screen_name
        if status.retweeted_status:
            status = status.retweeted_status
        if status.quoted_status:
            status = status.quoted_status
        text = status.full_text
        retweet_count = status.retweet_count
        status_id = status.id
        created_at = status.created_at
        link = status.urls
        if len(link) > 0:
            link = link[0].expanded_url
            page_title = self.get_page_title(link)
            if page_title:
                difference_seconds = self.get_time_difference(created_at)
                return [page_title, link, retweet_count, difference_seconds]

    def main_function(self):
        with open(self.TWITTER_CREDS_LOCATION) as f:
            twitter_credentials = json.load(f)
        api = twitter.Api(consumer_key=twitter_credentials['CONSUMER_KEY'],
                          consumer_secret=twitter_credentials['CONSUMER_SECRET'],
                          access_token_key=twitter_credentials['ACCESS_TOKEN'],
                          access_token_secret=twitter_credentials['ACCESS_TOKEN_SECRET'],
                          tweet_mode='extended')
        relevant_members = api.GetListMembers(list_id=self.TWITTER_LIST_ID)
        master_list = []
        for user in relevant_members:
            recent_tweets = api.GetUserTimeline(user_id=user.id)
            for status in recent_tweets:
                result = None
                result = self.pull_status(status)
                if result:
                    master_list.append(result)
        df = pd.DataFrame(master_list, columns=['title', 'link', 'retweets', 'seconds_since'])
        df = df[df['seconds_since'] <= self.time_limit]
        df = df.groupby(['title', 'link'])[['retweets', 'seconds_since']].max().reset_index()
        df = df.sort_values('retweets', ascending=False).reset_index(drop=True)
        with open(self.GOOGLE_SERVICE_CREDS_LOCATION) as f:
            service_account = json.load(f)
        spread = Spread(self.GOOGLE_SHEETS_ID, 
                        config=service_account,
                        sheet=self.sheet_name)
        spread.sheets.clear()
        update_time = datetime.strftime(datetime.now() - timedelta(hours=4), '%Y-%m-%d %H:%M:%S')
        update_time = f'Last Updated: {update_time} EST'
        spread.update_cells(start='A1', end='A1', sheet='last_updated', vals=[update_time])
        spread.df_to_sheet(df, index=False, sheet='news', start='A1')

if __name__ == "__main__":
    twitter_tool = TwitterPull()
    twitter_tool.main_function()