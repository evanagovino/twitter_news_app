App to pull out [links](https://help.twitter.com/en/using-twitter/twitter-lists) from a list of Twitter users and publish to a Google sheet.

The purpose of this project is to make a static webpage with news based on links tweeted out by a curated [list](https://help.twitter.com/en/using-twitter/twitter-lists) of Twitter. It pulls all links by these users (based on the last 20 tweets from each user), sorts by retweet count, and publishes them to a Google sheet. Note that it will only pull links if the page allows us to pull its HTML title - some publications like Bloomberg are blocking this script. 

Should be easily replicable - all you need is a 'twitter_credentials.json' file with Twitter developer credentials and a 'google_service_account.json' file that has Google service account credentials (for the Google sheets file). From there you can customize the Twitter list ID to your preferred list of users and the Google sheet ID to your spreadsheet. 

