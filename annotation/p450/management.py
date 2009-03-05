from django.dispatch import dispatcher
from django.db.models import signals
from annotate.p450 import models 

import os
import sys

from collections import defaultdict

def init_data():

    # connect to database
    import psycopg
    dbcon = psycopg.connect('') # TODO: insert database parameters
    dbcur = dbcon.cursor()

    ## First, get the interaction partners
    
    # retrieve proteins from the STRING db
    proteins = {}
    dbcur.execute("""SELECT protein_external_id, preferred_name, annotation FROM items.proteins WHERE species_id = 9606""")
    for (protein_external_id, preferred_name, annotation) in dbcur.fetchall():
        protein_id = protein_external_id.split(".", 1)[1]
        proteins[protein_id] = models.Protein(name = preferred_name, annotation = annotation, proteinid = protein_id)
        proteins[protein_id].save()
        
    # MeSH terms are also valid interaction partners    
    annotation = ""
    for line in open("/home/mkuhn/data/mesh/mesh_synonyms.dat"):
        (protein_id, preferred_name) = line.strip().split("\t")
        if protein_id not in proteins:
            proteins[protein_id] = models.Protein(name = preferred_name, annotation = annotation, proteinid = protein_id)
            proteins[protein_id].save()
    
    # foods are in a separate file
    foods = {}
    
    for line in os.popen("zcat /home/mkuhn/data/foodmining/alias4_uniq.tsv.gz"):
        (food_id, name) = line.strip("\n").split("\t")[1:3]
        
        if not (food_id and name): continue
        
        foods[food_id] = models.Food(name = name, foodid = food_id)
        foods[food_id].save()
        
    ## Finally, load the candidates
    for line in open("/home/mkuhn/src/action_annotation/django/annotate/p450/annotation_candidates.tsv"):
        (food, protein, score, sources) = line.strip().split("\t")
    
        x = models.Candidate(food = foods[food], protein = proteins[protein], sources = sources, score = float(score), annotation = "", from_abstract = "", from_file = False)
        x.save()


# this hook lets Django run the init_data function upon syncing the database
signals.post_syncdb.connect(init_data, sender=models)