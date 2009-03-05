#!/g/bork3/bin/python

## This script reads text-mining results and builds a smaller database of abstracts where the items are highlighted

import re
import sys
import os
from intervalmap import *
from collections import defaultdict

import psycopg2
dbcon = psycopg2.connect('') # TODO: insert db parameters
dbcur = dbcon.cursor()

# retrieve a list of interesting abstract ids
# this file is read later again, the format is: item1, item2, score, sources 
fh_interesting_abstracts = os.popen("cut -f 4 /home/mkuhn/src/action_annotation/django/annotate/p450/annotation_candidates.tsv | tr ',' '\n' | sort -u ")
interesting_abstract = fh_interesting_abstracts.next().strip()

abstract_item_names = defaultdict(list)

# load text-mining results
try:
    for line in os.popen("zcat /home/mkuhn/data/foodmining/textmining_complex.tsv.gz"):
        (abstract_id, _, item_id, name) = line.strip().split("\t")
    
        if abstract_id == interesting_abstract:
            abstract_item_names[abstract_id, item_id].append(name)
        else:
            while abstract_id > interesting_abstract:
                interesting_abstract = fh_interesting_abstracts.next().strip()
except StopIteration:
    pass            
    
print >> sys.stderr, "Abstracts/Items", len(abstract_item_names)


#### Generalized functions that work on multiple kinds of abstract data ####

class Abstract:
    def __init__(self, result):
        (self.abstract_id, self.publication_date, self.publication_source, self.linkout_url, self.title, self.body) = result
        self.title = str(self.title)
        self.body = str(self.body)
        self.score = 9999
            
    def __hash__(self):
        return hash(self.abstract_id)
    
    def __cmp__(self, other):
        return (cmp(self.score, other.score) or -cmp(self.publication_date, other.publication_date) 
                    or -cmp(self.abstract_id, other.abstract_id))
                    
    def clean(self):
        
        def _clean(t):
            t = t.replace("\n", "<br>")
            t = t.replace("'", "\\'")
            return t
            
        self.body = _clean(self.body)
        self.title = _clean(self.title)
            
def markup_and_find_names(names, name_color, name_type, text, distance):

    # Use an interval map to mark the character positions where a particular name 
    # matches. Because we are iterating from the longest string to the shortest,
    # short strings cannot match inside longer strings.
    name_pos = intervalmap()

    # Match lower-case, unaltered text
    original_text = text.lower()

    names_done = set()

    for (l, s) in reversed(names):
        # Note case-insensitevely if we have already worked on a certain name 
        lname = s.lower()
        if lname in names_done: continue
        names_done.add(lname)

        # Find all occurences of the string, and mark their positions
        start = 0
        to_find =  " %s " % s.lower()
        while 1:
            start = original_text.find(to_find, start)
            if start == -1: break

            end = start+l
            # Check that this character sequence is still free (but only at endpoints)
            if name_pos[start] == None and name_pos[end-1] == None:
                name_pos[start:end] = s

            start += l

        # Mark-up the abstract, also case-insensitive
        t = r"<span style='font-weight: bold; color: %s'>\1</span>" % (name_color[s], )
        re_name = re.compile(r"\b(%s)\b" % re.escape(s), re.I)
        text = re_name.sub(t, text)

    # Iterate through pairs of adjacent words. 
    positions = list(name_pos.items())
    for (left, right) in zip( positions[:-1], positions[1:] ):
        ((_, p1), w1) = left
        ((p2, _), w2) = right

        if name_type[w1] != name_type[w2]:
            # If the words are not synonymous, count the number of words == the number of spaces (-1)
            # between the two words. Also penalize the "." at the end of a sentence.
            distance = min(original_text.count(" ", p1, p2) + original_text.count(".", p1, p2), distance)

    # Remove extra spaces around punctuation marks
    text = re.sub(r"([[(]) ", r"\1", text) # ]")
    text = re.sub(r" ([.,):;\]])", r"\1", text)
    text = re.sub(r" ([-]) ", r"\1", text)

    return text, distance



def mark_abstract(food, protein, abstract_id):    

    # retrieve abstracts from the database (using STRING's database schema, see STRING homepage for documention)
    dbcur.execute("""SELECT abstract_id, publication_date, publication_source, linkout_url, title, body FROM raw_abstracts WHERE abstract_id = '%s'""" % abstract_id)
    x = dbcur.fetchone()
    if not x: return
    abstract = Abstract(x)

    abstract.food = food
    abstract.protein = protein

    abstract.food_synonyms = abstract_item_names[abstract_id, food]
    abstract.protein_synonyms = abstract_item_names[abstract_id, protein]

    name_color = {}
    name_type = {}
    names = []
    for s in abstract.food_synonyms:
        name_color[s] = "red"
        name_type[s] = 1
        names.append( (len(s), s) )
    
    for s in abstract.protein_synonyms:
        name_color[s] = "blue"
        name_type[s] = 2
        names.append( (len(s), s) )
        
    names.sort()
    
    # Mark-up both title and body of the abstract
    distance = len(abstract.body)
    (abstract.body, distance) = markup_and_find_names(names, name_color, name_type, abstract.body, distance)                
    (abstract.title, distance) = markup_and_find_names(names, name_color, name_type, abstract.title, distance)                
    
    # Punish empty abstracts
    if len(abstract.body) < 10: distance += 1000

    abstract.score = distance
    
    return abstract


# create SQL code for highlighted abstracts
i = 0

for line in open("/home/mkuhn/src/action_annotation/django/annotate/p450/annotation_candidates.tsv"):
    (food, protein, _, sources) = line.strip().split("\t")

    abstract_ids = sources.split(",")

    abstracts = []

    for abstract_id in abstract_ids[:250]:
        abstract = mark_abstract(food, protein, abstract_id)

        
        if abstract is not None:
            abstracts.append(abstract)
            
    for abstract in sorted(abstracts)[:50]:
        abstract.clean()
        print ("""
INSERT INTO abstracts VALUES (
	'%(abstract_id)s',
	'%(food)s',
	'%(protein)s',
	%(score)s,
	%(publication_date)s,
	'%(publication_source)s',
	'%(linkout_url)s',
	'%(title)s',
	'%(body)s'
); 
        """ % vars(abstract))

    print >> sys.stderr, i,
    sys.stderr.flush()
    i += 1
    

"""
CREATE TABLE abstracts (
	abstract_id character varying (20) NOT NULL,
	food character varying (20) NOT NULL,
	protein character varying (20) NOT NULL,
	distance int NOT NULL,
	publication_date int2,
	publication_source bytea,
	linkout_url bytea, 
	title bytea NOT NULL,
	body bytea NOT NULL
);

"""
