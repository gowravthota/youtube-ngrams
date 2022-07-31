import json
import requests
import re
from py_youtube import Data, Search
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from langdetect import detect


def get_all(wfile_name, search, limit):
    """
    Searches with youtube API, writes into json file.

    @:param file_name: text file name
    @:param search: youtube search keyword(s)
    @:param limit: number of videos
    @:return number of videos with valid subtitles
    """
    video_list = []
    videos = Search(search, limit).videos()
    for video in videos:
        if detect(video['title']) == 'en':
            try:
                data = collect(video['id'])
                if data['video_category'] != 'Music':
                    video_list.append(data['text'])
            except:
                pass
    with open(wfile_name, 'w', encoding='utf-8') as json_file:
        json_file.write(json.dumps(video_list))
    return len(video_list)


def collect(video_id):
    """
    Gets transcript of video.

    @:param video_id: youtube video ID
    @:return dictionary
    """
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    formatter = TextFormatter()
    text_formatted = clean_text(formatter.format_transcript(transcript))
    data = Data("https://youtu.be/" + video_id).data()
    dict = {
        'text': text_formatted,
        'video_id': video_id,
        'video_title': data['title'],
        'video_category': data['category']
    }
    return dict


def clean_text(transcript):
    """
    Cleans up text.

    @:param transcript: text to clean
    @:returns formatted text
    """
    transcript = re.sub("[\(\[].*?[\)\]]", "", transcript
                        .lower()
                        .strip()
                        .replace('\n', ' ')
                        .replace(' ', ' '))
    return transcript.translate(str.maketrans('', '', "!#$%&*+,-./:;<=>?@\^_`{|}~"))


def get_ngrams(rfile_name, search_word, search_range, ngram):
    """
    Get ngrams surrounding a keyword.

    @:param file_name: text file name
    @:param search_word: ngrams surrounding this keyword
    @:param search_range: n surrounding words
    @:param ngram: (n)-gram

    @:return ngram list
    """
    file = open(rfile_name)
    ngrams = []
    for text in json.load(file):
        result = [m.start() for m in re.finditer(search_word, text)]
        for index in result:
            left_index, right_index, right_space_counter, left_space_counter, right_space_counter, counter, flag \
                = 0, 0, 0, 0, 0, 1, True
            try:
                while flag:
                    if left_space_counter != search_range + 1:
                        new_index1 = index - counter
                        if text[new_index1] == " ":
                            left_space_counter += 1
                        if left_space_counter == search_range + 1:
                            left_index = new_index1
                    if right_space_counter != search_range + 1:
                        new_index2 = index + counter
                        if text[new_index2] == " ":
                            right_space_counter += 1
                        if right_space_counter == search_range + 1:
                            right_index = new_index2
                    else:
                        flag = False
                    counter += 1
                phrase = text[left_index + 1:right_index].split()
                output = []
                for i in range(len(phrase) - ngram + 1):
                    for word in phrase[i:i + ngram]:
                        if search_word in word:
                            output.append(phrase[i:i + ngram])
                ngrams.append(output)
            except:
                pass
    return ngrams


def get_common_ngrams(word, wfile_name, rfile_name):
    """
    Sorts bigrams and trigrams.

    @:param word: to search for
    @:param wfile_name: file to write
    @:param text_file_name: file to read
    """
    ngram_pop_list = []
    ngram_list = []
    # file, word, range, n-gram
    all_ngrams = get_ngrams(rfile_name, word, 2, 2) + get_ngrams(rfile_name, word, 2, 3)

    for i in all_ngrams:
        for j in i:
            ngram = " ".join(str(word) for word in j)
            url = f"https://books.google.com/ngrams/json?content={ngram}&year_start=1800&year_end=2000&corpus=26&smoothing=3"
            resp = requests.get(url)
            if resp.ok and len(json.loads(resp.content)) != 0:
                results = json.loads(resp.content)[0]['timeseries']
                if ngram not in ngram_list:
                    ngram_list.append(ngram)
                    ngram_pop_list.append((sum(results) / len(results), ngram))

    with open(wfile_name, 'w', encoding='utf-8') as json_file:
        json_file.write(json.dumps(sorted(ngram_pop_list)[::-1]))


if __name__ == "__main__":
    # usage
    get_common_ngrams('country', 'collection/common_ngrams.json', 'collection/collection.json')
    get_ngrams('collection/common_ngrams.json', 'country', 2, 2)
    get_all('collection/collection.json', 'podcast', 100)
