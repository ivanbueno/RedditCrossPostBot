import re
import sqlite3
import yaml
from random import choice, shuffle
from discordwebhook import Discord
from urllib.request import urlopen
import requests
import shutil
import os

class CrossPost:

    def __init__(
        self,
        reddit_instance,
        configuration
    ):
        self.configuration = configuration
        self.sources = {}
        self.reddit = reddit_instance
        self.updates = 0

        print('Loading database...')
        # Setup/Load SQL database
        self.sql = sqlite3.connect(self.configuration.get("default", "xpost_db"))
        self.c = self.sql.cursor()

        # Setup schema
        self.c.execute('CREATE TABLE IF NOT EXISTS posted(subm_id TEXT)')
        self.sql.commit()  # save the changes

        print('Loading schema...')
        self.schema = self.load_schema()

        print('Loading resources...')
        self.sources = self.load_resources()

    def load_schema(self):
        with open(self.configuration.get("default", "xpost_searches")) as file:
            return yaml.full_load(file).items()

    def is_search(self, item):
        search = None
        if "search" in item:
            search = item["search"]
        return search

    def load_resources(self):
        sources = {}
        source_processed = {}

        for destination, item in self.schema:
            search = self.is_search(item)

            for source in item["sources"]:
                submission_values = []

                source_key = source
                if search:
                    source_key = destination + '_' + source

                if source_key not in source_processed.keys():
                    print('-----')
                    print('Loading', source_key)
                    source_processed[source_key] = 1

                    submission_results = None
                    if search:
                        for s in search:
                            submission_results = self.reddit.subreddit(source).search(s)

                            for submission in submission_results:
                                submission_values.append(submission)
                                print('...', submission.title)
                    else:
                        submission_results = self.reddit.subreddit(source).hot()

                        for submission in submission_results:
                            submission_values.append(submission)
                            print('...', submission.title)

                    sources.update({source_key: submission_values})

        return sources
    
    def process(self):
        print('-----')
        print('Searching for posts...')
        for destination, item in self.schema:

            search = self.is_search(item)
            pattern = re.compile(r'\b({})\b'.format(r'|'.join(item["keywords"])), re.IGNORECASE)

            pattern_ignore = None
            if "ignore" in item:
                pattern_ignore = re.compile(r'\b({})\b'.format(r'|'.join(item["ignore"])), re.IGNORECASE)

            print('...', destination)
            for source in item["sources"]:

                if "random" in item and item["random"]:
                    if choice([True, False]):
                        print('      * RANDOM SKIP')
                        break

                throttle = None
                source_key = source
                if search:
                    source_key = destination + '_' + source
                    throttle = 1
                throttle_count = 1

                if "shuffle" in item:
                    shuffle(self.sources[source_key])

                for subm in self.sources[source_key]:
                    if search:
                        if throttle < throttle_count:
                            continue

                    self.c.execute('SELECT * FROM posted WHERE subm_id = ?', [subm.id])
                    if self.c.fetchone():  # skip the submission if it's already been posted
                        continue

                    if pattern_ignore:
                        if pattern_ignore.search(subm.title):
                            # then add the submission id to db
                            print('      ** Ignore')
                            self.marked_as_processed(subm.id)
                            continue

                    # then search for keywords
                    if pattern.search(subm.title):
                        print('      *', source, '--', subm.title)
                        if self.is_repost(destination, subm):
                            print('      ** Duplicate')
                            # then add the submission id to db
                            self.marked_as_processed(subm.id)
                            continue

                        if self.is_image(subm.url):
                            image_url = self.download_image(subm.url)

                            if image_url:
                                self.post_image(subm, destination, image_url)
                                throttle_count += 1

                                self.post_to_discord(item, subm.url)
                            else:
                                self.submit_post(subm, destination)
                                throttle_count += 1
                        else:
                            self.submit_post(subm, destination)
                            throttle_count += 1

    def marked_as_processed(self, id):
        self.c.execute('INSERT INTO posted VALUES(?)', [id])
        self.sql.commit()  # save the changes
                        
    def is_repost(self, destination, submission):
        submission_results = None
        submission_values = []
        if destination not in self.sources:
            submission_results = self.reddit.subreddit(destination).hot()

            for s in submission_results:
                submission_values.append(s)

            self.sources.update({destination: submission_values})

        for subm in self.sources[destination]:
            if subm.url == submission.url:
                return True

        return False

    def post_to_discord(self, item, url):
        if "discord" in item:

            if self.is_image(url):
                discord = Discord(url=item["discord"])
                discord.post(
                    embeds=[
                        {
                            "image": {"url": url},
                        }
                    ],
                )
                print('      ** Posted to discord.')

    def is_image(self, url):
        image_formats = ("image/png", "image/jpeg", "image/gif")
        site = ""
        try:
            site = urlopen(url)

            meta = site.info()  # get header of the http request

            if meta["content-type"] in image_formats:  # check if the content-type is a image
                return True

            print('      ** Not an image')
            return False
        except Exception as e:
            print('      ** Cannot fetch image')
            return False

    def download_image(self, image_url):
        filename = image_url.split("/")[-1]

        # Open the url image, set stream to True, this will return the stream content.
        r = requests.get(image_url, stream = True)

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            
            # Open a local file with wb ( write binary ) permission.
            with open(filename,'wb') as f:
                shutil.copyfileobj(r.raw, f)
                
            return os.path.realpath(f.name)
        else:
            return False

    def post_image(self, submission, destination, url):

        try:
            self.reddit.subreddit(destination).submit_image(title=submission.title, image_path=url, send_replies=False, without_websockets=True)
            os.remove(url)

            self.marked_as_processed(submission.id)

            self.updates += 1
        except Exception as e:
            print('            ', e)

    def submit_post(self, submission, destination):
        try:
            print('      ** Crossposting') 
            crosspost = submission.crosspost(subreddit=destination, send_replies=False)
            self.marked_as_processed(submission.id)
            self.updates += 1
        except Exception as e:
            print('            ', e)