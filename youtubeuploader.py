#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################################################################
#                                                                              #
# (c) 2017 by Andrea Marcelli                                                  #
# TDPuploader is distributed under a BSD-style license -- See file LICENSE.md  #
#                                                                              #
################################################################################

import httplib
import httplib2
import os
import random
import sys
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

import coloredlogs
import logging

log = logging.getLogger()
coloredlogs.install(fmt='%(asctime)s %(levelname)s:: %(message)s',
                        datefmt='%H:%M:%S', level='INFO', logger=log)


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
                        httplib.IncompleteRead, httplib.ImproperConnectionState,
                        httplib.CannotSendRequest, httplib.CannotSendHeader,
                        httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "my_client_secret.json"
MISSING_CLIENT_SECRETS_MESSAGE = "MISSING_CLIENT_SECRETS_MESSAGE"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

def get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def initialize_upload(youtube, title, description):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': 27
        },
        'status': {
            'privacyStatus': 'public',
            'license': 'creativeCommon'
            'embeddable': True
        }
    }

    csize = 1024*1024

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.file, chunksize=csize, resumable=True)
    )

    resumable_upload(insert_request)


def resumable_upload(insert_request):
    ''' This method implements an exponential backoff strategy to resume a
        failed upload.'''
    response = None
    error = None
    retry = 0
    while response is None:
        try:
            log.info("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    log.info("Video id '%s' was successfully uploaded.", response['id'])
                else:
                    log.error("The upload failed with an unexpected response: %s", response)
                    sys.exit(1)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            log.error(error)
            retry += 1
            if retry > MAX_RETRIES:
                log.error("No longer attempting to retry.")
                sys.exit(1)

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            log.info("Sleeping %f seconds and then retrying...", sleep_seconds)
            time.sleep(sleep_seconds)


if __name__ == '__main__':
    argparser.add_argument("--file", required=True, help="Video file to upload")
    argparser.add_argument("--title", help="Video title", default="Test Title")
    argparser.add_argument("--description", help="Video description",default="Test Description")
    args = argparser.parse_args()

    if not os.path.exists(args.file):
        log.error("Please specify a valid file using the --file= parameter.")
        sys.exit(1)

    log.info("File size: %d", os.path.getsize(args.file))

    youtube = get_authenticated_service(args)
    try:
        initialize_upload(youtube, args.title, args.description)
    except HttpError, e:
        print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
