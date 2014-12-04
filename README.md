# Blubbstrahl

This script can download photos from a twitter stream.

# Installation
You will need to have the Python Twitter Tools installed. I also didn't test with Python versions below 3.4 yet.

# How to use it?
First you need to create a file named `config.ini`.
See the included example as to what you'll need to input.
Then you need to create your own app credentials
and enter them in the config.
The `access_token` field can be left as it is. This will be used by the script for storing a received access token (sometime in the future).

After editing the config you can start downloading the photos of a specific user like this:
`python blubbstrahl.py -u username`

# Limitations
For now the script will only get the 100 newest tweets and download all attached images, if there are any. This includes retweets.
This limit will be changed later, but as there seems to be a limit imposed by twitter on how many tweets you can get via the API (3000?) it will probably never be possible to download all photos the user has ever uploaded. Also private accounts are not possible yet.
