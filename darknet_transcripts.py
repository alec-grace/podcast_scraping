# File: darknet_transcripts.py
# Author: Alec Grace
# Created: 13 Feb 2024
# Purpose:
#   Provide functions necessary to deal with downloading Darknet Diaries
#   podcast transcripts and converting them to text files
import os
import re
import time

import requests
from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

from main import get_podcast_config


# gets the most recent darknet episode to keep up-to-date
def get_latest_ep(config):
    base_url = config["url"]
    page = requests.get(base_url + "/episode/")
    soup = BeautifulSoup(page.content, 'html.parser')
    failed = True

    # get list of relative link for most recent episode (first on page)
    while failed:
        latest_ep = soup.find("a", href=True, string=re.compile("EP *"))
        if latest_ep:
            failed = False
        else:
            print("Waiting to try again...")
            time.sleep(10)
    return latest_ep


# get each url for the specified darknet episodes
def get_dn_episodes(config):
    episodes = []
    # determine what the selection of episodes is: add each link to the return list
    if config["all_episodes"]:
        raw = str(get_latest_ep(config))
        newest = raw[raw.index("href=") + 15: raw.index(">") - 2]
        newest = int(newest)
        for i in range(1, newest + 1):
            episodes.append(i)
    elif config["range"]:
        start = int(config["episode_range"].split(',')[0])
        end = int(config["episode_range"].split(',')[1])
        for i in range(start, end + 1):
            episodes.append(i)
    else:
        eppy_list = config["select_episodes"]
        for eppy in eppy_list:
            episodes.append(int(eppy))

    print("darknet episodes collected")
    return episodes


# write each darknet transcript to text file from the html
# change this to use requests.get('url', allow_redirects=True) when time allows
def get_dn_text(config):
    # set up driver for browser
    driver = webdriver.Chrome()
    episodes = get_dn_episodes(config)
    for i in episodes:
        # first check to see if the file exists, and if it's empty, delete it
        ep_text = "dn/episode" + str(i) + ".txt"
        if os.path.isfile(ep_text):
            with open(ep_text, 'r') as infile:
                file_contents = infile.read()
                if not file_contents:
                    os.remove(ep_text)
                else:
                    continue
        # direct the driver to the transcript url and pull the html
        url = config["sel_url"] + "transcript/" + str(i) + "/"
        driver.get(url)
        time.sleep(1)
        try:
            element = driver.find_element(By.TAG_NAME, 'pre')
        except selenium.common.exceptions.NoSuchElementException:
            element = driver.find_elements(By.TAG_NAME, 'p')
        with open("dn/episode" + str(i) + ".txt", 'a') as outfile:
            try:
                outfile.write(element.text)
            except AttributeError:
                for item in element:
                    outfile.write(item.text)
        # sleep to limit chance of 429 response
        time.sleep(3)

    driver.quit()
    print("dn text files done")