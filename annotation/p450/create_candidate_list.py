#!/usr/bin/env python
# encoding: utf-8

## A script to extract a candidate list from the STRING textmining files

import sys
import os

from collections import defaultdict

protein_whitelist = (
"D000815", "D001141", "D001141", "D001189", "D001579", "D002786", "D002790", "D003577", "D013250", "D013252", "D013253", "D013254", "D013255", "D015090", "D019362", "D019363",
"D019388", "D019389", "D019392", "D019405", "D019405", "D019475", "D039181", "D050564", "D050564", "D051544", "D053493", "ENSP00000310149", "ENSP00000310721",
"ENSP00000311095", "ENSP00000314398", "ENSP00000318867", "ENSP00000321821", "ENSP00000324648", "ENSP00000325822", "ENSP00000330650", "ENSP00000332679", "ENSP00000333212",
"ENSP00000333534", "ENSP00000334246", "ENSP00000334592", "ENSP00000337915", "ENSP00000338087", "ENSP00000342007", "ENSP00000346625", "ENSP00000347011", "ENSP00000348380",
"ENSP00000358903", "ENSP00000360247", "ENSP00000360317", "ENSP00000360372", "ENSP00000360958", "ENSP00000360991", "ENSP00000364304", "ENSP00000366903", "ENSP00000368079",
"ENSP00000369050", "ENSP00000372812", "ENSP00000373426", "ENSP00000373995", "ENSP00000374478", "ENSP00000374621", "ENSP00000001146", "ENSP00000003100", "ENSP00000011989",
"ENSP00000216862", "ENSP00000221700", "ENSP00000222382", "ENSP00000222982", "ENSP00000224356", "ENSP00000228606", "ENSP00000248041", "ENSP00000252909", "ENSP00000252945",
"ENSP00000258415", "ENSP00000260433", "ENSP00000260630", "ENSP00000260682", "ENSP00000261835", "ENSP00000265302", "ENSP00000269703", "ENSP00000275016", "ENSP00000285949",
"ENSP00000285979", "ENSP00000292414", "ENSP00000294342", "ENSP00000301141", "ENSP00000301173", "ENSP00000301645",
)                     
                      
def main():           
                
                
    food_blacklist = [ line.strip() for line in os.popen("cat ~/mkuhn/*annotation.tsv | grep 'blacklist food' | cut -f 1 | sort -u") ]
    protein_blacklist = [ line.strip() for line in os.popen("cat ~/mkuhn/*annotation.tsv | grep 'blacklist protein' | cut -f 2 | sort -u") ]
                      
    start = 0         
    size = 2000       
                      
    scores = {}       
    sources = {}
    
    for line in os.popen("zcat /home/mkuhn/data/foodmining/textmining_interact.cooccur.tsv.gz | grep -v '\t-4\t' | egrep '\t(-2|9606)\t[NS]'"):
        (food, protein, _score, source) = line.strip().split("\t")[2:]
        
        if protein in protein_whitelist: continue
        # if protein not in protein_whitelist: continue
        
        if protein in protein_blacklist or food in food_blacklist: continue
        
        score = float(_score)

        if (protein, food) in scores:
            scores[protein, food] = 1 - (1 - scores[protein, food]) * (1 - score)
            sources[protein, food] = sources[protein, food] + "," + source
        else:
            scores[protein, food] = score
            sources[protein, food] = source
        
    print >> sys.stderr, "scores", len(scores)
    
        
    fh_out = open("annotation_candidates.tsv", "w")
            
    for (score, protein, food) in sorted( ((score, protein, food) for ((protein, food), score) in scores.iteritems()), reverse = True )[start:start+size]:
        
        source = ",".join( sorted( sources[protein, food].split(","), reverse = True ) )
         
        print >> fh_out, "%(food)s\t%(protein)s\t%(score)g\t%(source)s" % locals()
        
    
    
    

if __name__ == '__main__':
    main()

