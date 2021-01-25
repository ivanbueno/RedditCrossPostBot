import sqlite3
import yaml
from discordwebhook import Discord
import feedparser
from urllib.request import urlopen

class RssPost:

    def __init__(
        self,
        configuration
    ):
        self.configuration = configuration
        self.updates = 0

        print('Loading database...')
        # Setup/Load SQL database
        self.sql = sqlite3.connect(self.configuration.get("default", "rss_db"))
        self.c = self.sql.cursor()

        # Setup schema
        self.c.execute('CREATE TABLE IF NOT EXISTS posted(subm_id TEXT)')
        self.sql.commit()  # save the changes

        print('Loading schema...')
        self.schema = self.load_schema()

    
    def load_schema(self):
        with open(self.configuration.get("default", "rss_searches")) as file:
            return yaml.full_load(file).items()

    def process(self):

        for key, item in self.schema:
            d = feedparser.parse(item['rss'])

            count = 1
            limit = 1
            for entry in d["entries"]:

                self.c.execute('SELECT * FROM posted WHERE subm_id = ?', [entry["title"]])
                if self.c.fetchone():
                    continue

                if count > limit:
                    break

                self.post_to_discord(item, entry)
                count += 1

    def post_to_discord(self, item, entry):
        if "discord" in item:

            content = {
                        "title": entry["title"],
                        "description": entry["summary"],
                        "url": entry["link"],
                    }

            if "news_image" in entry:
                if self.is_image(entry["news_image"]):
                    content["image"] = {"url": entry["news_image"]}

            discord = Discord(url=item["discord"])
            discord.post(
                embeds=[content],
            )
            print('Discord:', entry["title"])
                
            # then add the submission id to db
            self.c.execute('INSERT INTO posted VALUES(?)', [entry["title"]])
            self.sql.commit()  # save the changes

            self.updates += 1

    def is_image(self, url):
        image_formats = ("image/png", "image/jpeg", "image/gif")
        site = urlopen(url)
        meta = site.info()  # get header of the http request
        if meta["content-type"] in image_formats:  # check if the content-type is a image
            return True

        return False