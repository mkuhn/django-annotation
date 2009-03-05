# encoding: utf-8
# Create your views here.

from django.template import Context, loader
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Q

from annotate.p450 import models 

import psycopg
dbcon = psycopg.connect('') # TODO insert database
dbcur = dbcon.cursor()

import re

from collections import defaultdict
import sys


## Helper code to color sentences

colors = (
"LightGreen",
"LightPink",
"LightSalmon",
#"LightSeaGreen",
"LightSkyBlue", 
#"LightSlateBlue", 
#"LightSlateGray", 
"LightSteelBlue",
)            


span1a = """<span onmouseout="this.style.background = 'white';" onmouseover="this.style.background = 'LightGrey';">"""
def span1b(i):
    color = colors[i % len(colors) ]
    return """<span style="background: %s" onmouseout="this.style.background = '%s';" onmouseover="this.style.background = 'LightGrey';">""" % (color, color)
span2 = "</span>"

# Identify sentence boundaries. Ignore tags!
re_mask_sentence = re.compile(r"\. ((<[^>]*>)?[^a-z<])")
# Check if highlighted words of both colors occur in any order
re_has_both_kinds = re.compile(r"color: blue'>.*color: red'>|color: red'>.*color: blue'>")    

def highlight_abstract(body):
    count = 0
    sentences = []
    for sentence in re_mask_sentence.sub(r".¤\1", body).split("¤"):
        if re_has_both_kinds.search(sentence):
            sentences.append("".join( (span1b(count), sentence, span2)) )
            count += 1 
        else:
            sentences.append("".join( (span1a, sentence, span2)) )
        
    return "\n".join(sentences)



def candidate_export(request):

    fh_out = open("TODO/p450_annotation.tsv", "w")

    for annotation in models.Candidate.objects.all():
        print >> fh_out, annotation 


def candidate(request, object_id):
    
    
    t = loader.get_template('p450/candidate_detail.html')
        
    object = models.Candidate.objects.filter(id=object_id)[0]
    food = object.food.foodid
    protein = object.protein.proteinid

    annotations = defaultdict(lambda : defaultdict(bool))

    # possible_annotations = ("substrate", "substrate/inducer", "substrate/inhibitor", "inducer", "inhibitor", "not relevant")
    possible_annotations = ("substrate", "inducer", "inhibitor", "indirect inducer", "indirect inhibitor", "other interaction", "controversial", "not relevant")

    # also write to a log, just to be sure
    fh_log = open("TODO/p450_annotation.log", "a")

    to_next = False

    if request.GET:

        if "annotation" in request.GET:
    
            object.annotation = request.GET["annotation"]
            object.from_abstract = request.GET["abstract_id"]
            object.from_file = False

            print >> sys.stderr, "ANN", request.GET["annotation"], request.GET["abstract_id"], food, protein
            print >> fh_log, "ANN", request.GET["annotation"], request.GET["abstract_id"], food, protein

            to_next = True

            object.save()
    
        if request.GET.get("ignore_food"):
            print >> fh_log, "BL_FOOD", food
            
            for candidate in models.Candidate.objects.filter(food=food):
                candidate.annotation = "blacklist food"
                candidate.from_file = False
                candidate.save()

            to_next = True

        if request.GET.get("ignore_protein"):
            print >> fh_log, "BL_PROTEIN", protein
                        
            for candidate in models.Candidate.objects.filter(protein=protein, annotation=""):
                candidate.annotation = "blacklist protein"
                candidate.from_file = False
                candidate.save()

            to_next = True
            
    fh_log.close()

    # should we go to the next annotation candidate?
    if to_next:
        
        next = models.Candidate.objects.filter(Q(annotation="") | Q(from_file=True))[0]
        print >> sys.stderr, "REDIR", next
        
        return HttpResponseRedirect("../%d/" % next.id)
        
            

    # print >> sys.stderr, annotations

    abstracts = []
    
    # get all abstracts from the database and show them to the user
    dbcur.execute("""SELECT abstract_id, distance, publication_date, publication_source, linkout_url, title, body FROM abstracts WHERE food = '%s' AND protein = '%s'""" % (str(food), str(protein)))
    for (abstract_id, score, publication_date, publication_source, linkout_url, title, body) in dbcur.fetchall():

        p = { 
            'abstract_id' : abstract_id,
            'score' : score
         }

        body = highlight_abstract(body)

        abstract = "<h3>%(title)s</h3><p>%(body)s</p>" % locals()

        p["abstract"] = abstract

        l = [] 
         
        for annotation in possible_annotations:
            
            
            if annotation == object.annotation:
                s = "<a href='?annotation=%s&abstract_id=%s'><span style=\"font-weight: bold; color: red;\">%s</span></a> " % (annotation, abstract_id, annotation)
            else:
                s = "<a href='?annotation=%s&abstract_id=%s'>%s</a> " % (annotation, abstract_id, annotation)
                
        
        
            l.append(s)
        
        p["annotation_links"] = " &mdash; ".join(l) 
        
        abstracts.append(p)
    
    # print >> sys.stderr, proteins
    # print >> sys.stderr, annotations
    
    if not abstracts and not object.annotation:
        object.annotation = "no abstract"
        object.save()
        next = models.Candidate.objects.filter(annotation="")[0]
        print >> sys.stderr, "REDIR", next
        
        return HttpResponseRedirect("../%d/" % next.id)
    
    c = Context(locals())
    return HttpResponse(t.render(c))
