import sys, getopt, os
import subprocess
import requests
import json
import re

# Needs requests module. 'pip install requests' on the server

# Constants
ACCESS_TOKEN = os.environ['GITHUB_OAUTH_TOKEN']
UPLOAD_FILE = sys.argv[1]
REPO_OWNER = "umarniz" # https://github.com/umarniz/GithubReleaseSystem
REPO_NAME = "GithubReleaseSystem"

if UPLOAD_FILE == '':
    print "Exiting - No upload file name provided."
    sys.exit(2)

print "File to upload " + UPLOAD_FILE

# Helper to upload release file
def UploadRelease(url, filePath, fileName):
    print "Uploading release asset"

    # Remove curly braces from url
    p = re.compile('\{.*?\}', re.DOTALL)
    url = p.sub('', url)

    # Set up for query parameters
    url = url + "?"

    # File to upload
    data = open(filePath, 'rb').read()

    # Upload release asset
    r = requests.post(url + "name=" + fileName, headers={'Content-Type': 'application/octet-stream', "Authorization":"token " + ACCESS_TOKEN}, data=data)
    print (r.status_code, r.reason)

    if r.status_code // 100 != 2:
        print "Failed to upload release: " + r.reason
        return False

    print "Successfully uploaded release!"
    return True


# Get Git TAG
process = subprocess.Popen(['git', 'describe', '--tag'], stdout=subprocess.PIPE)
tag_id, err = process.communicate()

# Remove newline in the end
tag_id = tag_id.rstrip()

print "Making release for tag " + tag_id

# Check if its a pre release
is_pre_release = False
if "rc" in tag_id:
    is_pre_release = True

# Read changes file to post release notes
f = open('changes.md', 'r')
release_message = f.read()

r = requests.post("https://api.github.com/repos/" + REPO_OWNER + "/" + REPO_NAME + "/releases?access_token=" + ACCESS_TOKEN, json={'tag_name': tag_id, 'name': tag_id, 'body': release_message, 'prerelease': is_pre_release})
print(r.status_code, r.reason)

if r.status_code // 100 == 2:
    response = r.json()
    upload_url = response['upload_url']

    UploadRelease(upload_url, UPLOAD_FILE, tag_id + ".zip")
else:
    print "Aborting. Failed to create release: " + r.reason

##If you wan't to debug the request
# try:
#     from http.client import HTTPConnection
# except ImportError:
#     from httplib import HTTPConnection
# HTTPConnection.debuglevel = 1
