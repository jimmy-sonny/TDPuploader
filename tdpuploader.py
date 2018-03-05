#!/usr/bin/env python3
# -*- coding: utf-8 -*-

################################################################################
#                                                                              #
# (c) 2017 by Andrea Marcelli                                                  #
# TDPuploader is distributed under a BSD-style license -- See file LICENSE.md  #
#                                                                              #
################################################################################

import sys
assert sys.version_info >= (3, 4)

import signal
import argparse
from bs4 import BeautifulSoup
import requests

import coloredlogs
import logging
log = None

__version = 0.1

banner = '''
TDPuploader - Upload TdP lesssons on your Youtube channel
by Andrea Marcelli (!) v.%s
'''

tdp_url = "https://elite.polito.it/teaching/current-courses/164-03fyz-tecn-progr?showall=&start=7"


def signal_handler(signal, frame):
    log.critical('You pressed Ctrl+C!')
    log.critical('Finishing')
    sys.exit(0)


def upload_lecture(title, description):
    log.warning("TODO!")


def select_and_fill_lecture_info(candidate_lectures):
    indexes = [cc['index'] for cc in candidate_lectures]
    correctInput = False
    while not correctInput:
        data = input("Choose a lecture (range: %d-%d):\n" %
                     (min(indexes), max(indexes)))
        try:
            choice = int(data)
            if choice in indexes:
                correctInput = True
            else:
                log.warning("Insert an integer in the correct range!!")
        except ValueError:
            log.warning("Insert an integer!!")

    log.info("Your choice: %d", choice)
    cc = candidate_lectures[choice - 1]
    log.info(cc)

    title = "TdP-2017-%s%02d: %s" % (cc['type'],
                                     cc['lecture_number'], cc['summary'].split()[0])
    log.info("Suggested title: \"%s\"", title)
    
    title_confirmed = False
    while not title_confirmed:
        reply = str(input("Confirm title: \"%s\"" % title + ' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            title_confirmed = True
        if reply[:1] == 'n':
            title = input("Enter the new title:\n")
    log.warning("TITLE: \"%s\"", title)

    log.warning("DESCRIPTION:")
    if cc['type'] == "L":
        l_type = "Lezione"
    elif cc['type'] == "EA":
        l_type = "Esercitazione in aula"
    description = "%s n.%02d del %s: %s" % (
        l_type, cc['lecture_number'], cc['date'], cc['summary'])
    description += "\n\nTecniche di Programmazione, anno 2017/2018"
    description += "\nIngegneria Gestionale, Politecnico di Torino"
    description += "\nSito web corso: http://bit.ly/tecn-progr"
    print(description)

    return title, description


def parse_registro(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    registro_div = soup.find('div', attrs={'itemprop': 'articleBody'})
    found = False
    for h2 in registro_div.find('h2'):
        if h2 == "Registro":
            log.info("Found \"Registro\" TDP")
            found = True
            break
    if not found:
        log.error("Cannot find \"Registro\"")
        sys.exit(1)

    log.info("Parsing \"Registro\" TDP")
    table = registro_div.find('table')
    table_body = table.find('tbody')
    rows = table_body.find_all('tr')

    counter = 0
    lecture_number = 0
    candidate_lectures = list()
    try:
        for row in rows:
            raw_cols = row.find_all('td')
            cols = [x.text.strip() for x in raw_cols]
            if cols[2] != "EL":
                lecture_number += 1

            # Se e' segnata una lezione (L, EA), ma non c'e' un video associato
            if (cols[0]) and (not cols[4]) and (cols[2] != "EL"):
                counter += 1
                cc = dict()
                cc['index'] = counter
                cc['lecture_number'] = lecture_number
                cc['date'] = cols[0]
                cc['time'] = cols[1]
                cc['type'] = cols[2]
                cc['summary'] = cols[3]
                cc['lecturer'] = cols[6]
                log.info(" ".join([str(x) for x in cc.values()]))
                candidate_lectures.append(cc)
    except:
        log.exception("Parsing Regisro TDP caused an exception")
        sys.exit(1)
    log.info("Found %d candidate lectures", len(candidate_lectures))
    return candidate_lectures


def main():
    ''' That's main! '''
    parser = argparse.ArgumentParser(description='TDPuploader')
    parser.add_argument('-d', '--debug', dest='debug',
                        action='store_true', help='Log level debug')
    args = parser.parse_args()

    global log
    log = logging.getLogger()
    coloredlogs.install(fmt='%(asctime)s %(levelname)s:: %(message)s',
                        datefmt='%H:%M:%S', level='INFO', logger=log)

    log.info("Donwloading Rgistro TDP")
    page = requests.get(tdp_url)
    if page.status_code != 200:
        log.error("Cannot dowload the tdp page")
        sys.exit(1)

    cl = parse_registro(page.content)
    t, d = select_and_fill_lecture_info(cl)
    upload_lecture(t, d)


if __name__ == '__main__':
    print(banner % __version)
    signal.signal(signal.SIGINT, signal_handler)
    main()
