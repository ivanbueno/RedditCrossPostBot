from datetime import datetime, timedelta
import praw
from pathlib import Path
from configparser import ConfigParser
from classes.crosspost import CrossPost

def main():
    configuration = ConfigParser()
    configuration.read(Path(__file__).resolve().with_name("crosspost.ini"))

    reddit = praw.Reddit(
        client_id=configuration.get("default", "client_id"),
        client_secret=configuration.get("default", "client_secret"),
        password=configuration.get("default", "password"),
        user_agent=configuration.get("default", "user_agent"),
        username=configuration.get("default", "username"),
    )

    try:
        crosspost = CrossPost(reddit, configuration)
        crosspost.process()
    except Exception as e:
        print('Error: {}'.format(e))

    print('-----------------')
    print(crosspost.updates, 'crossposts performed.')
    print('Next run is on', (datetime.now() + timedelta(minutes=30)).strftime("%B %d, %Y  %I:%M %p"))

if __name__ == '__main__':
    main()
