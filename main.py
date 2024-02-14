import json
import os.path
from darknet_transcripts import *
from west_wing_transcripts import *


# comment about function function
# load json into a list of podcast information
def load_json():
    with open("config.json", 'r') as config:
        data = json.load(config)
    config.close()
    return data


# get the config information on a specific podcast
def get_podcast_config(data: list[dict], title):
    for item in data:
        if item["title"] == title:
            return item


# do some rudimentary cleaning (to be updated when specific use case for data is known)
def clean(config):
    for file in os.listdir(config["text_destination"]):
        with open(config["text_destination"] + file, "r") as cur_file:
            new_lines = []
            lines = cur_file.readlines()
            for line in lines:
                # remove stage directions
                new_line = re.sub("[\[].*?[\]]", "", line).rstrip("\n").rstrip(" ")
                # I have no idea what this is but it kept showing up and i don't want it so i'm removing it
                new_line = new_line.replace(" ", " ")
                new_lines.append(new_line)
        cur_file.close()

        # rewrite the file with cleaned transcript
        with open(config["text_destination"] + file, "w") as outfile:
            for line in new_lines:
                outfile.write(line)
        outfile.close()


def main():
    # load config data
    json_data = load_json()["sites"]

    # load west wing data, get the pdfs, convert to text, and clean text transcripts
    westwing = get_podcast_config(json_data, "west wing")
    get_ww_transcript_pdfs(westwing)
    ww_to_text(westwing)
    clean(westwing)

    # load darknet data, get the text transcripts, clean transcripts
    darknet = get_podcast_config(json_data, "darknet")
    get_dn_episodes(darknet)
    clean(darknet)


if __name__ == "__main__":
    main()
