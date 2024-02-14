import os
import re
import time

import PyPDF2
import requests
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup


# pull the pdf file of each west wing episode specified in config.json
# store it in the specified pdf file directory
def get_ww_transcript_pdfs(config):
    base_url = "http://thewestwingweekly.com"
    page = requests.get(base_url + "/index")
    soup = BeautifulSoup(page.content, 'html.parser')
    failed = True

    # get list of relative links for each episode
    while failed:
        epies = soup.find_all("a", class_="archive-item-link")
        if epies:
            failed = False
        else:
            print("Waiting to try again...")
            time.sleep(10)

    # create list of FULL urls for each episode
    ep_page_urls = []
    for ep in epies:
        ep = str(ep)
        begin = ep.rindex("href=") + 6
        end = ep.index(">") - 1
        ep_num = ep[begin + 10:end]
        # don't add episodes known to have no transcript
        if ep_num in config["no_transcript"]:
            continue
        if config["all_episodes"]:
            ep_page_urls.append(base_url + ep[begin:end])
        elif config["select"]:
            if ep_num in config["select_episodes"]:
                ep_page_urls.append(base_url + ep[begin:end])
        else:
            if ep_num in config["season_list"]:
                ep_page_urls.append(base_url + ep[begin:end])

    # remove any episodes that have already been downloaded
    remove_pages = []
    for ep in ep_page_urls:
        if os.path.isfile(config["pdf_destination"] + ep[38:] + ".pdf"):
            remove_pages.append(ep)

    for page in remove_pages:
        print("Removing: " + page)
        ep_page_urls.remove(page)

    # pull each transcript and place in "ww" folder
    for ep_page in ep_page_urls:
        print("Current: " + ep_page[38:])
        failed = True
        tries = 0
        while failed:
            episode = requests.get(ep_page)
            # check for "too many requests" error
            if episode == "<Response [429]>":
                time.sleep(15)
                failed = True
                continue
            soup_page = BeautifulSoup(episode.content, 'html.parser')
            # use pattern matching instead of exact string
            trial = soup_page.find('a', string=re.compile('transcript*'))
            # wait if first 4 searches don't find the link - sometimes the page doesn't load idk
            if trial is None:
                if tries > 3:
                    failed = False
                    print("skipping episode: " + ep_page)
                else:
                    failed = True
                    print("no transcript found for " + ep_page + ".", end='')
                    print(".", end='')
                    time.sleep(1)
                    print(".", end='')
                    time.sleep(1)
                    print(".")
                    tries += 1
                    # sleep to minimize 429 error
                    time.sleep(10)
            else:
                download = base_url + trial.get('href')
                # sleep to minimize 429 error
                time.sleep(7)
                failed = False
        if tries <= 3:
            # if it doesn't time out then download the pdf
            contents = requests.get(download).content
            with open(config["pdf_destination"] + ep_page[38:] + ".pdf", "wb") as file:
                file.write(contents)
                file.close()

    print("ww init pdfs done")


# get specific pdf transcripts that either failed or were not complete
def get_select_ww_pdfs(config, episodes: list[str]):
    base_url = "http://thewestwingweekly.com"
    page = requests.get(base_url + "/index")
    soup = BeautifulSoup(page.content, 'html.parser')
    failed = True

    # get list of relative links for each episode
    while failed:
        epies = soup.find_all("a", class_="archive-item-link")
        if epies:
            failed = False
        else:
            print("Waiting to try again...")
            time.sleep(10)

    # create list of FULL urls for each episode
    ep_page_urls = []
    for ep in epies:
        ep = str(ep)
        begin = ep.rindex("href=") + 6
        end = ep.index(">") - 1
        if ep[begin + 10:end] in episodes:
            ep_page_urls.append(base_url + ep[begin:end])
            print("Added: " + base_url + ep[begin:end])

    # pull each transcript and place in "destination" folder
    for ep_page in ep_page_urls:
        print("Current: " + ep_page[38:])
        failed = True
        tries = 0
        while failed:
            episode = requests.get(ep_page)
            # check for "too many requests" error
            if episode == "<Response [429]>":
                time.sleep(15)
                failed = True
                continue
            soup_page = BeautifulSoup(episode.content, 'html.parser')
            # use pattern matching instead of exact string
            trial = soup_page.find('a', string=re.compile('transcript*'))
            # wait if first 4 searches don't find the link - sometimes the page doesn't load idk
            if trial is None:
                if tries > 3:
                    failed = False
                    print("skipping episode: " + ep_page)
                else:
                    failed = True
                    print("no transcript found for " + ep_page + ".", end='')
                    print(".", end='')
                    time.sleep(1)
                    print(".", end='')
                    time.sleep(1)
                    print(".")
                    tries += 1
                    # sleep to minimize 429 error
                    time.sleep(10)
            else:
                download = base_url + trial.get('href')
                # sleep to minimize 429 error
                time.sleep(7)
                failed = False
        # if it doesn't time out then download the pdf
        if tries <= 3:
            contents = requests.get(download).content
            with open(config["pdf_destination"] + ep_page[38:] + ".pdf", "wb") as file:
                file.write(contents)
                file.close()

    print("ww retry pdfs done")


# convert the west wing pdf transcripts to text
def ww_to_text(config):
    try_again = True
    while try_again:
        retry = []
        for file in os.listdir(config["pdf_destination"]):
            try:
                # pull text from pdf
                reader = PdfReader(config["pdf_destination"] + file)
                length = len(reader.pages)
                text_file = "ww_text/" + file[:-4] + ".txt"
                # check if text transcript already exists
                if not os.path.isfile(text_file):
                    # write the contents to text file
                    with open(text_file, 'a') as outfile:
                        for i in range(length):
                            outfile.write(reader.pages[i].extract_text())
                    print("Finished " + text_file)
                    outfile.close()
            # if a file can't be read, retry the download
            except PyPDF2.errors.PdfReadError:
                os.remove("ww/" + file)
                retry.append(file[:-4])
        if not retry:
            try_again = False
            continue
        # if there are any episodes that failed, retry them
        if retry:
            get_select_ww_pdfs(retry)
    print("ww text files done")
