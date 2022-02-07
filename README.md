# AMI-Topic-Segmentation-Processor
Download and Process [AMI Corpus](https://groups.inf.ed.ac.uk/ami/corpus/) for Topic Segmentation

## AMI Meeting Corpus
* [Link](https://groups.inf.ed.ac.uk/ami/corpus/)
* Number of meetings after preprocessing : 139

## Requirements
Tested on Python3.8
```
pip install -r requirements.txt
```

## How to Use
Download and collect topics from each meeting
```
python download_and_process.py
```
* Original AMI Corpus will be downloaded into : `data/ami_public_manual_1.6.2`.
* Meeting transcription after processing: `data/transcripts`.


Each meeting with topics can be found in `data/transcripts/{meeting_id}.json`.
In `{meeting_id}.json` are list of topics :
```
[                                                    
 {
  "topic_idx": "top.4",
  "topic_type": "other",
  "other_description": "introduction of participants and their roles",
  "sentences": [
   {
    "filename": "ES2002a.B.words.xml",
    "start_word": 0,
    "end_word": 71,
    "text": "Okay . Right . [vocalsound] Um well this is the kick-off meeting for our our project . Um [vocalsound] and um this is just what we're gonna be doing over the next twenty five minutes . Um so first of all , just to kind of make sure that we all know each other , I'm Laura and I'm the project manager . [vocalsound] Do you want to introduce yourself again ?"
   }, 
   ...
   
  ], # dialogue in topic
  "sub_topics":[] # sub topics are also list of topics
 }, # topic end
 ...
 
]
```



## Acknowledgement
If you use the AMI Meeting Corpus, please add the citation:
```
@INPROCEEDINGS{Mccowan05theami,
    author = {I. Mccowan and G. Lathoud and M. Lincoln and A. Lisowska and W. Post and D. Reidsma and P. Wellner},
    title = {The AMI Meeting Corpus},
    booktitle = {In: Proceedings Measuring Behavior 2005, 5th International Conference on Methods and Techniques in Behavioral Research. L.P.J.J. Noldus, F. Grieco, L.W.S. Loijens and P.H. Zimmerman (Eds.), Wageningen: Noldus Information Technology},
    year = {2005}
}
```
