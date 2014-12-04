import configparser, json, os, urllib.request, argparse
from twitter import *

class Blubbstrahl:
    def __init__(self):
        self.consumer_key = ''
        self.consumer_secret = ''
        self.oauth_token = ''
        self.oauth_secret = ''
        self.access_token = None
        self.client = None
        self.download_path = None

    def read_config(self, config_file):
        # Use RawConfigParser because ConfigParser will try to use interpolation
        # (% signs will be interpreted as references. we don't want that.)
        config = configparser.RawConfigParser()
        config.read(config_file)

        if not config.has_section('login'):
            print("Missing 'login' section in config.")
            exit()

        if not config.has_option('login','consumer_key'):
            print("Missing 'consumer_key' entry in login section of config.")
            exit()

        if not config.has_option('login','consumer_secret'):
            print("Missing 'consumer_secret' entry in login section of config.")
            exit()

        if not config.has_section('general'):
            print("Missing 'general' section in config.")
            exit()

        if not config.has_option('general','download_path'):
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
        #if self.client is not None:
        #    return self.client

        # Login and get a new access token if we don't have one
        # Then return the AppClient
        """
        if self.access_token is (None or ""):
            self.client = AppClient(self.consumer_key, self.consumer_secret)
            print("Client: {0}".format(self.client))
            #self.access_token = self.client.get_access_token()
        else:
            self.client = AppClient(self.consumer_key,
                self.consumer_secret, self.access_token)
        """
        #auth=OAuth(self.oauth_token, self.oauth_secret,
        #            self.consumer_key, self.consumer_secret)
        #self.client = Twitter(auth)
        self.client = Twitter(auth=OAuth(self.oauth_token, self.oauth_secret,
                    self.consumer_key, self.consumer_secret))

        return self.client

    def find_photos(self, data, entity_key, url_set):
        # Check if tweet contains any entities
        if entity_key in data:
            # Check if tweet contains media in entities
            if 'media' in data[entity_key]:
                for m in data[entity_key]['media']:
                    # We only want original size photos
                    if m['type'] == 'photo':
                        img_url = "{0}:{1}".format(m['media_url'],"orig")
                        #print(img_url)
                        url_set.add(img_url)


    def get_photoset(self, twitter_handle):

        #print("Using Access Token: {0}".format(self.client.get_access_token()))
        # Get tweets from a user
        #response = blubbstrahl.client.api.statuses.user_timeline.get(
        #    screen_name=twitter_handle)

        response = self.client.statuses.user_timeline(
            screen_name=twitter_handle,
            count=100)
        #with open('output_all.json','w+') as f:
        #    json.dump(response, f)
        #print(response.data[0]['extended_entities'])
        all_urls = set()
        # Search for photos in all received tweets
        for data in response:
            #print(data.id)
            #with open('output.json','w+') as f:
            #    json.dump(data, f)

            self.find_photos(data, 'entities', all_urls)

            self.find_photos(data, 'extended_entities', all_urls)

        return all_urls

    def download_file(self, url, path):
        if not os.path.exists(path):
            os.makedirs(path)

        file_name = os.path.join(path, url.split('/')[-1].split(':')[0])

        print("Downloading {0} to {1}".format(url, file_name))
        with open(file_name, "wb") as local_file:
            f = urllib.request.urlopen(url)
            local_file.write(f.read())

    def download_photos(self, twitter_handle):
        print("Downloading photos of {0}".format(twitter_handle))
        all_urls = self.get_photoset(twitter_handle)

        if all_urls is not None:
            for img_url in all_urls:
                path = os.path.join(blubbstrahl.download_path, twitter_handle)
                self.download_file(img_url, path)

        else:
            print("Didn't find any images.")


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Download photos from twitter.")
    parser.add_argument('user', help="Twitter username from which to download")
    args = parser.parse_args()
    twitter_handle = args.user

    blubbstrahl = Blubbstrahl()
    blubbstrahl.read_config("config.ini")
    blubbstrahl.create_client()

    blubbstrahl.download_photos(twitter_handle)


    blubbstrahl.write_config("config.ini")
