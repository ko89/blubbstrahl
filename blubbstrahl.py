import configparser
import os
import urllib.request
import argparse
import tweepy
import pickle


class Blubbstrahl:
    def __init__(self):
        self.consumer_key = ''
        self.consumer_secret = ''
        self.oauth_token = ''
        self.oauth_secret = ''
        self.access_token = None
        self.client = None
        self.download_path = None
        self.last_tweets = {}

    def read_config(self, config_file):
        """Open ini-file and read all config values."""

        # Use RawConfigParser because ConfigParser
        # will try to use interpolation.
        # (% signs will be interpreted as references.
        # we don't want that.)
        config = configparser.RawConfigParser()
        config.read(config_file)

        if not config.has_section('login'):
            print("Missing 'login' section in config.")
            exit()

        if not config.has_option('login', 'consumer_key'):
            print("Missing 'consumer_key' entry in login section of config.")
            exit()

        if not config.has_option('login', 'consumer_secret'):
            print("Missing 'consumer_secret' \
                entry in login section of config.")
            exit()

        if not config.has_section('general'):
            print("Missing 'general' section in config.")
            exit()

        if not config.has_option('general', 'download_path'):
            print("Missing 'download_path' in general section of config.")
            exit()

        self.consumer_key = config['login']['consumer_key']
        print("Read consumer key: {0}".format(self.consumer_key))
        self.consumer_secret = config['login']['consumer_secret']
        print("Read consumer secret: {0}".format(self.consumer_secret))
        self.access_token = config['login']['access_token']
        print("Read access token: {0}".format(self.access_token))
        self.oauth_token = config['login']['oauth_token']
        self.oauth_secret = config['login']['oauth_secret']
        self.download_path = config['general']['download_path']

    def read_pickle(self, picklefile):
        """Read the dictionary of last read tweets from file"""
        try:
            with open(picklefile, 'rb') as f:
                self.last_tweets = pickle.load(f)
        except IOError as err:
            print('I/O error while reading file with last tweets.')
            print('Error #{0}: {1}'.format(err.errno, err.strerror))
            print("The script will probably run fine,")
            print("but it doesn't know which tweets")
            print("were already found last time.")

    def write_pickle(self, picklefile):
        """Write the dictionary of last read tweets to file"""
        with open(picklefile, 'wb') as f:
            pickle.dump(self.last_tweets, f)

    def write_config(self, config_file):
        config = configparser.RawConfigParser()

        config['login'] = {'consumer_key': self.consumer_key,
                           'consumer_secret': self.consumer_secret,
                           'oauth_token': self.oauth_token,
                           'oauth_secret': self.oauth_secret,
                           'access_token': self.access_token}

        config['general'] = {'download_path': self.download_path}

        with open(config_file, 'w+') as configfile:
            config.write(configfile)

    def create_client(self):
        """Create a new twitter client instance."""

        # Login and get a new access token if we don't have one
        # Then return the AppClient
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.oauth_token, self.oauth_secret)

        self.client = tweepy.API(
            auth,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True)

        return self.client

    def find_photos(self, data, entity_key, url_set):
        """Search a single tweet for photos."""
        # Check if tweet contains any entities
        if entity_key in data._json:
            # Check if tweet contains media in entities
            if 'media' in data._json[entity_key]:
                for m in data._json[entity_key]['media']:
                    # We only want original size photos
                    if m['type'] == 'photo':
                        img_url = "{0}:{1}".format(m['media_url'], "orig")
                        url_set.add(img_url)

    def get_photoset(self, twitter_handle, maxitems, use_last_tweets):
        """Retrieve a set of photo-urls by the user."""

        # Use a set to prevent duplicate entries
        all_urls = set()
        s_id = 0

        cursor = tweepy.Cursor(self.client.user_timeline,
                               id=twitter_handle)

        if use_last_tweets is True and \
                twitter_handle in self.last_tweets:
            s_id = self.last_tweets[twitter_handle]
            cursor = tweepy.Cursor(self.client.user_timeline,
                                   id=twitter_handle,
                                   since_id=s_id,
                                   count=maxitems)

        # Search for photos in all received tweets
        for data in cursor.items(maxitems):

            # Photo urls can be in two sections of the
            # returned json.

            self.find_photos(data, 'entities', all_urls)

            self.find_photos(data, 'extended_entities', all_urls)
            if twitter_handle in self.last_tweets:
                if data.id > self.last_tweets[twitter_handle]:
                    self.last_tweets[twitter_handle] = data.id
            else:
                self.last_tweets[twitter_handle] = data.id

        return all_urls

    def download_file(self, url, path):
        """Download a photo from twitter."""
        if not os.path.exists(path):
            os.makedirs(path)

        file_name = os.path.join(path, url.split('/')[-1].split(':')[0])

        print("Downloading {0} to {1}".format(url, file_name))
        with open(file_name, "wb") as local_file:
            f = urllib.request.urlopen(url)
            local_file.write(f.read())

    def download_photos(self, twitter_handle, items, use_last_tweets):
        """Search and download the specified number of photos of the user."""
        all_urls = self.get_photoset(twitter_handle, items, use_last_tweets)

        if all_urls is not None:
            for img_url in all_urls:
                path = os.path.join(blubbstrahl.download_path, twitter_handle)
                self.download_file(img_url, path)
        else:
            print("Didn't find any images.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download photos \
                                    from twitter.")
    parser.add_argument('user', help="Twitter username from which to download")
    parser.add_argument('--continue_mode', '-c', action='store_true',
                        help="Use this, if only tweets newer than those\
                         already searched last time should be read.")
    parser.add_argument('--items', '-i', nargs='?', const=500, type=int,
                        help="Specify the number of tweets to read.\
                              (Default is 500)")
    args = parser.parse_args()
    twitter_handle = args.user
    use_last_tweets = args.continue_mode
    maxitems = args.items

    blubbstrahl = Blubbstrahl()
    blubbstrahl.read_config("config.ini")
    blubbstrahl.read_pickle("last_tweets.pickle")
    blubbstrahl.create_client()

    print("Downloading photos of the last {0} tweets of {1}".format(
        maxitems, twitter_handle))
    if use_last_tweets is True and len(blubbstrahl.last_tweets) > 0:
        print("Continuing from last read tweet if possible.")

    blubbstrahl.download_photos(twitter_handle, maxitems, use_last_tweets)

    blubbstrahl.write_config("config.ini")
    blubbstrahl.write_pickle("last_tweets.pickle")
