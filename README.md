# Reddit CrossPost Bot (Reddit XPost Bot)
A Reddit bot that searches for **[keywords]** in the title of a **[source]** subreddit, and crossposts the results to a **[destination]** subreddit.

## Installation

### Requirements
* python3
* pip install praw
* pip install pyyaml

### Configuration

1. Copy crosspost.ini.sample to crosspost.ini
2. Fill the following values:
```
[default]
xpost_db=/full/path/to/crosspost.db
xpost_searches=/full/path/to/crosspost.yaml
client_id=
client_secret=
user_agent=
username=
password=
```
*crosspost.db will be automatically created if it doesn't exist.*

3. Copy crosspost.yaml.sample to crosspost.yaml.
4. Setup the destination subreddit, keywords, and source subreddit.
```
destinationsubreddit1:
  keywords:
    - Keyword to Search For
    - Another keyword
  sources:
    - subredditsource1
    - subredditsource2
fruitsalad:
  keywords:
    - apple
    - orange
  sources:
    - fruitstand
    - trees
```

* Multiple destinations, keywords, and sources can be set.
* In the example above, crosspost bot will search for "apple" and "orange" in the titles of the hottest post from "fruitstand" and "trees" subreddits.
* If posts are found with the matching keywords, the bot will crosspost (xpost) the submissions to "fruitsalad" subreddit.

### Tips
* Add your bot as a moderator to the destination subreddit to prevent any throttling restrictions.

### References
* [Comprehensive Guide to Running your Bot](https://www.reddit.com/r/RequestABot/comments/3d3iss/a_comprehensive_guide_to_running_your_bot_that/)
* [Register your bot](https://www.reddit.com/prefs/apps/)
