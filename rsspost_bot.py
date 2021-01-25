from pathlib import Path
from configparser import ConfigParser
from classes.rsspost import RssPost

def main():
    configuration = ConfigParser()
    configuration.read(Path(__file__).resolve().with_name("rsspost.ini"))

    try:
        rsspost = RssPost(configuration)
        rsspost.process()
    except Exception as e:
        print('Error: {}'.format(e))

    print('-----------------')
    print(rsspost.updates, 'crossposts performed.')

if __name__ == '__main__':
    main()
