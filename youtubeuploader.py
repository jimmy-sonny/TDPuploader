#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################################################################
#                                                                              #
# (c) 2017 by Andrea Marcelli                                                  #
# TDPuploader is distributed under a BSD-style license -- See file LICENSE.md  #
#                                                                              #
################################################################################

import http.client
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
logging.getLogger('googleapicliet.discovery_cache').setLevel(logging.ERROR)

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
                        http.client.IncompleteRead, http.client.ImproperConnectionState,
                        http.client.CannotSendRequest, http.client.CannotSendHeader,
                        http.client.ResponseNotReady, http.client.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

MISSING_CLIENT_SECRETS_MESSAGE = "MISSING_CLIENT_SECRETS_MESSAGE"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def get_authenticated_service(client_secret):
    flow = flow_from_clientsecrets(client_secret,
                                   scope=YOUTUBE_UPLOAD_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                 http=credentials.authorize(httplib2.Http()))


def initialize_upload(youtube, file, title, description):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'categoryId': 27
        },
        'status': {
            'privacyStatus': 'public',
            'license': 'creativeCommon',
            'embeddable': True
        }
    }

    csize = 1024 * 1024 * 2

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(file, chunksize=csize, resumable=True)
    )
    log.info("Uploading file...")
    resumable_upload(insert_request, os.path.getsize(file) / (1024 * 1024))


def resumable_upload(insert_request, file_size):
    ''' This method implements an exponential backoff strategy to resume a
        failed upload.'''
    response = None
    error = None
    retry = 0
    mb_counter = 0
    while response is None:
        try:
            status, response = insert_request.next_chunk()
            mb_counter += 2
            percentage = mb_counter / file_size * 100
            log.info("Percentage: %.1f", percentage)

            if response is not None:
                if 'id' in response:
                    log.info(
                        "Video id '%s' was successfully uploaded.", response['id'])
                else:
                    log.error(
                        "The upload failed with an unexpected response: %s", response)
                    sys.exit(1)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (
                    e.resp.status, e.content)
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

    log.info("Uploading finished")
    print(response)


def upload_lecture(title, description, client_secret, video_path):
    ''' Upload the selected video on YouTubne '''

    youtube = get_authenticated_service(client_secret)
    try:
        initialize_upload(youtube, video_path, title, description)
    except HttpError as e:
        log.error("An HTTP error %d occurred:\n%s" %
                  (e.resp.status, e.content))
