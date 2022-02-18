import os
import sys
import re
import json
from collections import defaultdict
from tqdm import tqdm
from bs4 import BeautifulSoup
class Word():
    def __init__(self, text, order, start_time, end_time, punc=None):
        self.text = str(text)
        self.order = int(order)
        self.start_time = float(start_time) if start_time is not None else None
        self.end_time = float(end_time) if end_time is not None else None
        self.punc = punc

    def __str__(self):
        return f"{self.text}\t, {self.order}, {self.start_time}->{self.end_time}, punc={self.punc}"

def write_json(data, path, verbose=False):
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)

def download_corpus(ami_dir):
    import urllib.request
    import zipfile

    '''
        This function is modified from : 
            https://github.com/gcunhase/AMICorpusXML/blob/master/AMICorpusHandler.py
    '''
    download_link = 'http://groups.inf.ed.ac.uk/ami/AMICorpusAnnotations/ami_public_manual_1.6.2.zip'
    if not os.path.exists(ami_dir):
        os.makedirs(ami_dir, exist_ok=True)
        print(f"Downloading AMI Corpus to: {ami_dir}")
        zipped_ami_filename = ami_dir + '.zip'
        urllib.request.urlretrieve(download_link, zipped_ami_filename)
        
        # unzip
        zip_ref = zipfile.ZipFile(zipped_ami_filename, 'r')
        zip_ref.extractall(ami_dir)
        zip_ref.close()

        # delete zip file
        os.remove(zipped_ami_filename)
    else:
        print(f"AMI Corpus has already been downloaded in: {ami_dir}")

def read_xml_file(path):
    with open(path, 'r') as f:
        content = f.readlines()
        content = ''.join(content)
    return content

def read_default_topic(path):
    def parse_topic(elem, default_topic):
        idx = elem.get('nite:id')
        name = elem.get('name')
        default_topic[idx] = name
        for sub_elem in elem.find_all('topicname'):
            parse_topic(sub_elem, default_topic)

    content = read_xml_file(path)
    soup = BeautifulSoup(content, 'lxml')

    default_topic = {}
    parse_topic(soup.find('topicname'), default_topic)
    return default_topic

def parse_transcription(path):
    content = read_xml_file(path)
    soup = BeautifulSoup(content, 'lxml')
    words= []
    for elem in soup.body.find('nite:root').findAll():
        word_id = re.sub('[a-zA-Z0-9]+\.[A-E]\.words', '', elem.get('nite:id'))
        if re.search('[^0-9]+', word_id):
            # some nite:id are [a-zA-Z0-9]+\.[A-E]\.wordsx, such as IS1000a.A.words.xml
            continue
        else:
            word_id = int(word_id)

        start_time = elem.get('starttime')
        end_time = elem.get('endtime')
        if end_time is None:
            end_time = start_time
        is_punc = elem.get('punc') 

        if elem.name == 'w':
            text = elem.text
        else:
            text = f'[{elem.name}]'
        
        w = Word(text, word_id, start_time, end_time, is_punc)

        while len(words) < word_id:
            words.append(Word('', len(words), None, None, None))
        assert len(words) == word_id, (elem)
        words.append(w)

    return words

def parse_transcription_from_meeting(transcript_dir, meeting_id, debug=False):
    if debug :
        print ('meeting_id : ', meeting_id)
    # iterate transcriptions having the same meeting_id
    transcripts = {}
    for filename in os.listdir(transcript_dir):
        if meeting_id in filename:
            if debug :
                print (f'parse words from : {filename}')
            transcripts[filename] = parse_transcription(os.path.join(transcript_dir, filename))
    return transcripts

def parse_topic(elem, default_topic):
    # 1. get topic type and description
    # pointer example : 
    #   <nite:pointer href="default-topics.xml#id(top.11)" role="scenario_topic_type"></nite:pointer>

    pointer = elem.find('nite:pointer')
    if pointer is None:
        # some topic file doesn't has pointer tag ... such as TS3012b.topic.xml
        # use description to find topic type
        desc = elem.get('description') 
        topic_idx = [k for k, v in default_topic.items() if v == desc]
        if len(topic_idx) == 0:
            # some descriptions are not in default topic
            topic_desc = desc 
            topic_idx='top.4' # top.4 is 'other'
        else:
            topic_idx = topic_idx[0]
            topic_desc = None

        topic_type = default_topic[topic_idx] 

    else:
        href = pointer.get('href')
        topic_idx = re.search("top\.[0-9]+", href).group()
        topic_type = default_topic[topic_idx]
        topic_desc = elem.get('other_description')

    # 2. parse sentence
    sentences = []
    for row in elem.find_all('nite:child'):
        href = row.get('href')
        ret = re.search('([a-zA-Z0-9]+\.[A-Z]\.words\.xml)#id\([a-zA-Z0-9]+\.[A-Z]\.words([0-9]+)\)(\.\.id\([a-zA-Z0-9]+\.[A-Z]\.words([0-9]+)\))?', href)
        filename = ret.group(1)
        start_word = ret.group(2)
        end_word = ret.group(4)
        end_word = start_word if end_word is None else end_word
       
        sentences.append({'filename':filename, 'start_word':int(start_word), 'end_word':int(end_word)})

    # 3. some topics has sub-topics, recursice process sub-topics
    sub_topics = []
    for sub_elem in elem.find_all('topic'):
        sub_topics.append(parse_topic(sub_elem, default_topic))
        
    topic = {'topic_idx':topic_idx,
             'topic_type':topic_type,
             'other_description':topic_desc, 
             'sentences':sentences,
             'sub_topics':sub_topics}
    return topic

def parse_topic_from_meeting(meeting_path, default_topic, transcript_dir, debug=False):
    def get_sentence_from_transcript(topic):
        for sentence in topic['sentences']:
            filename = sentence['filename']
            start_word = sentence['start_word']
            end_word = sentence['end_word']
            sentence_text = ' '.join([transcripts[filename][i].text for i in range(start_word, end_word+1)])
            sentence['text'] = sentence_text

        for sub_topic in topic['sub_topics']:
            get_sentence_from_transcript(sub_topic)

    # get transcriptions of each speaker
    meeting_id = os.path.basename(meeting_path).split('.')[0]
    if debug :
        print (f'Parsing topic of meeting {meeting_id}')
    transcripts = parse_transcription_from_meeting(transcript_dir, meeting_id, debug=debug)

    # parse meeting topic file
    content = read_xml_file(meeting_path)
    soup = BeautifulSoup(content, 'lxml')
    topics = []
    for elem in soup.body.find('nite:root').find_all('topic'):
        # parse topic
        topic = parse_topic(elem, default_topic)

        # extract sentences from transcriptions
        get_sentence_from_transcript(topic)
        topics.append(topic)

    return topics

if __name__ == '__main__':
    ami_dir = 'data/ami_public_manual_1.6.2'
    transcript_output_dir = 'data/transcripts'

    download_corpus(ami_dir)
    topic_dir = os.path.join(ami_dir, 'topics')
    transcript_dir = os.path.join(ami_dir, 'words')
    
    # extract topic information and structure
    default_topic_path = os.path.join(ami_dir,'ontologies','default-topics.xml')
    default_topic = read_default_topic(default_topic_path)
    for filename in tqdm(os.listdir(topic_dir)):
        meeting_id = filename.split('.')[0]
        topic_path = os.path.join(topic_dir, filename)
        
        # parse topic structure from topic file
        topics = parse_topic_from_meeting(topic_path, default_topic, transcript_dir)

        # save to file
        output_path = os.path.join(transcript_output_dir, f'{meeting_id}.json')
        write_json(topics, output_path)
