import re
import sqlite3
import yaml

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

    def load_resources(self):
        sources = {}
        source_processed = {}

        for destination, item in self.schema:
            search = None
            if "search" in item:
                search = item["search"]

            for source in item["sources"]:
                submission_values = []

                if source not in source_processed.keys():
                    print('-----')
                    print('Loading', source)
                    source_processed[source] = 1

                    submission_results = None
                    if search:
                        submission_results = self.reddit.subreddit(source).search(search)
                    else:
                        submission_results = self.reddit.subreddit(source).hot()

                    for submission in submission_results:
                        submission_values.append(submission)
                        print('...', submission.title)

                    sources.update({source: submission_values})

        return sources
    
    def process(self):
        print('-----')
        print('Searching for posts...')
        for destination, item in self.schema:
            pattern = re.compile(r'\b({})\b'.format(r'|'.join(item["keywords"])), re.IGNORECASE)

            pattern_ignore = None
            if "ignore" in item:
                pattern_ignore = re.compile(r'\b({})\b'.format(r'|'.join(item["ignore"])), re.IGNORECASE)

            print('...', destination)
            for source in item["sources"]:

                for subm in self.sources[source]:
                    self.c.execute('SELECT * FROM posted WHERE subm_id = ?', [subm.id])
                    if self.c.fetchone():  # skip the submission if it's already been posted
                        continue

                    if pattern_ignore:
                        if pattern_ignore.search(subm.title):
                            continue

                    # then search for keywords
                    if pattern.search(subm.title):
                        print('      *', source, '--', subm.title)
                        self.submit_post(subm, destination)

    def submit_post(self, submission, destination):
        try:
            crosspost = submission.crosspost(subreddit=destination, send_replies=False)

            # then add the submission id to db
            self.c.execute('INSERT INTO posted VALUES(?)', [submission.id])
            self.sql.commit()  # save the changes

            self.updates += 1
        except Exception as e:
            print('            ', e.message)