import sys, getopt, os
import subprocess
import json
import re
import zipfile
import shutil
import urllib2

# Constants
GithubAccessToken = 'YOUR_READ_ONLY_ACCESS_TOKEN'
SenseSDKVersion = sys.argv[1]
Configuration = sys.argv[2]
VersionFileName = 'libs/Sense/sense_sdk_version.txt'
DestDir = os.path.abspath("libs/Sense")
RepoURL = "https://api.github.com/repos/YOUR_NAME/YOUR_REPO"

# Argument check
if SenseSDKVersion == '':
    print "Exiting - No Sense SDK version provided."
    sys.exit(2)

# Setup variables
doDownloadSDK = True
fileList=[]

# Check if we have the right version
if os.path.isfile(VersionFileName):
    # Read lines in the file
    fileList = [line.rstrip('\n') for line in open(VersionFileName)]
    lastVersion = fileList[0]
    fileList.pop(0)

    if lastVersion == SenseSDKVersion or lastVersion == SenseSDKVersion + " " + Configuration :
        doDownloadSDK = False
        print "Skipping download, Sense SDK UP-TO-DATE"
    else:
        print "SDK Version changed to " + SenseSDKVersion + "_" + Configuration
        os.remove(VersionFileName)

if doDownloadSDK:

    # Cleanup
    for file in fileList:
        shutil.rmtree(DestDir + "/" + file)

    # Download SDK
    finalURL = RepoURL + '/releases/tags/' + SenseSDKVersion + '?access_token=' + GithubAccessToken

    try:
        req = urllib2.urlopen(finalURL)
    except urllib2.HTTPError, ev:
        print "Got an error response: " + str(ev.code) + " from server. Are you sure that " + SenseSDKVersion + " is a tagged build on github for Sense iOS SDK?"
        sys.exit(2)

    print "Downloading SDK " + SenseSDKVersion
    zipFilePath = os.path.abspath(SenseSDKVersion + '.zip')

    # Download the asset file
    assetData = json.load(req)
    assetUrl = assetData['assets'][0]['url'] + "?access_token=" + GithubAccessToken

    assetReq = urllib2.Request(assetUrl, headers={'Accept':'application/octet-stream'})
    try:
        assetResp = urllib2.urlopen(assetReq)
        CHUNK = 16 * 1024
        with open(zipFilePath, 'wb') as f:
            while True:
              chunk = assetResp.read(CHUNK)
              if not chunk: break
              f.write(chunk)
    except urllib2.HTTPError, ev:
        print "Error code: " + str(ev.code) + " when trying to download asset! "
        sys.exit(2)

    print "Extracting SDK"

    # We use OS calls as there is bug in the zip module that it doesn't respect
    # file permissions in the zip file causing frameworks to fail on run time.
    sdkTempPath = os.path.abspath("libs/sense_sdk")
    subprocess.call(["mkdir", "-p", sdkTempPath])
    subprocess.call(["unzip", zipFilePath, "-d", sdkTempPath])

    print "Cleaning up"
    os.remove(zipFilePath)

    fileNames = []

    srcDir = os.path.abspath("libs/sense_sdk/" + Configuration)

    # Support for old releases which didn't have Debug releases
    ignoreConfiguration = False
    if os.path.isdir(srcDir) == False:
        srcDir = os.path.abspath("libs/sense_sdk/Release")
        ignoreConfiguration = True
        print "WARNING: This release for Sense iOS SDK doesn't have debug symbols!"

    if not os.path.isdir(DestDir):
        os.makedirs(DestDir)

    # iOS SDK files are in a release folder, so lets move them
    src_files = os.listdir(srcDir)
    for file_name in src_files:
        full_file_name = os.path.join(srcDir, file_name)
        fileNames.append(file_name)
        shutil.move(full_file_name, DestDir)

    shutil.rmtree("libs/sense_sdk")

    # Write file names to the version file to be able to clean properly in the future
    with open(VersionFileName, 'w') as vFile:
        if ignoreConfiguration:
            vFile.write(SenseSDKVersion + '\n')
        else:
            vFile.write(SenseSDKVersion + " " + Configuration + '\n')

        for filename in fileNames:
            vFile.write(filename + '\n')

    print "Successfully setup Sense SDK " + SenseSDKVersion
