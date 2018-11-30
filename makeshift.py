#!/usr/bin/env python
# coding: utf-8
import json
import random
from collections import deque
import glob
import os
import re
import spacy

def load_spacy():
    print("loading spacy")
    return spacy.load("en_core_web_md")

def load_apprentice_sents(nlp):
    print("loading apprentice")
    apprentice = json.load(open("sources/apprentice_eps.json"))
    txt = " ".join([ep['summary'].replace(
        "<p>","").replace(
            "</p>", "").replace(
                "&amp;", "&") for ep in apprentice])
    doc = nlp(txt)
    return apprentice, list(doc.sents)

def load_kleiser(nlp):
    print("loading Kleiser")
    phrases = open("sources/kleiser_phrases.txt").readlines()
    return [nlp(phrase) for phrase in phrases]

def find_kleisers(sent, sources):
    matches = deque()
    for (i, p) in enumerate(sources['kleiser']):
        sim = sent.similarity(p)
        bestsim = matches[0][1] if matches else 0
        if sim > bestsim:
            matches.extendleft([[i, sim, p]])
        if len(matches) > 20:
            matches.pop()
    return matches

def find_kleisers2(sent, sources):
    pairs = [(i, s.similarity(sent), s) for (i, s) \
             in enumerate(sources['kleiser'])]
    return [p for p in sorted(pairs, key=lambda x: -x[1])[:50]]

def load_repub(nlp):
    print("loading Repub")
    repubfiles = glob.glob("sources/repub_1*")
    repubtext = ""
    for fname in repubfiles:
        with open(fname) as f:
            lines = f.readlines()
            repubtext += " ".join(lines[1:])
    repubtext = repubtext.replace("\n", " ")
    return nlp(repubtext)

def find_repubs(sent, sources):
    pairs = [(i, s.similarity(sent), s) for (i, s) \
             in enumerate(sources['repub'].sents)]
    return [p for p in sorted(pairs, key=lambda x: -x[1])[:60]]

def prepare_conwell_model(nlp):
    acrestext = open("sources/conwell_sents.txt").read()
    acrestext = acrestext.replace("\n", " ")
    conwell = nlp(acrestext)
    conwell.vocab.to_disk("sources/conwell.vocab")
    conwell.to_disk("sources/conwell.model")

def load_conwell(nlp):
    print("loading Conwell")
    if not (os.path.exists("sources/conwell.model") and \
            os.path.exists("sources/conwell.vocab")):
        prepare_conwell_model(nlp)
    convocab = spacy.vocab.Vocab().from_disk("sources/conwell.vocab")
    return spacy.tokens.Doc(convocab).from_disk("sources/conwell.model")

def find_conwell(sent, sources):
    pairs = [(i, s.similarity(sent), s) for (i, s) \
             in enumerate(sources['conwell'].sents)]
    return [p for p in sorted(pairs, key=lambda x: -x[1])[:100]]

def generate_text(sources, RANDOM_SEED=1100):
    print("generating text with seed {}".format(RANDOM_SEED))
    random.seed(RANDOM_SEED)
    txt = ""
    for (i, sent) in enumerate(sources['sents']):
        print(i, end=" ", flush=True)
        if (i % 4 == 0):
            para = "   " + sources['apprentice'][i//4]['name'] + "\n\n"
        else:
            para = ""
        kmatches = find_kleisers(sent, sources)
        kmatches2 = find_kleisers2(sent, sources)
        if (i % 7 == 0):
            anyconwellphrase = random.choice(list(sources['conwell'].sents))
            anynext = find_kleisers2(anyconwellphrase, sources)
            anyphrase = anyconwellphrase.text + " "
            if anynext:
                anyphrase += anynext[0][2].text.capitalize() + ". "
        else:
            anykleiserphrase = random.choice(sources['kleiser'])
            anynext = find_kleisers2(anykleiserphrase, sources)
            anyphrase = anykleiserphrase.text.capitalize() + ". " 
            if anynext:
                anyphrase += anynext[1][2].text.capitalize() + ". "
    
        rmatches = find_repubs(sent, sources)
        rmatch = random.choice(rmatches)
    
        conwells = find_conwell(sent, sources)
    
        para += kmatches2[0][2].text + ", "
        para += kmatches[-4][2].text + ", "
        para += kmatches[-3][2].text + ", "
        para += kmatches[-1][2].text + ". "
        if len(kmatches) > 12:
            para += kmatches[-10][2].text.capitalize() + ". "
        para += rmatch[2].text + " "
        para += random.choice(kmatches2[1:5])[2].text + ".\n\n"
    
        para += anyphrase
        para += sent.text + " "
        para += random.choice(conwells[:15])[2].text + " " 
        para += random.choice(conwells[15:50])[2].text + " " 
        para += kmatches[1][2].text + ". "
        para += kmatches[2][2].text + ".\n\n"
        txt  += para
    return txt

def clean_text(txt):
    print("clean text")
    txt = txt.replace(" i ", " I ")
    txt = txt.replace("    ", " ").replace("   ", " ").replace("  ", " ")
    txt = txt.replace("\n,", ",").replace("\n.", ".")
    txt = txt.replace(" , ", ", ").replace(" . ", ". ")
    txt = txt.replace("?. ", "? ").replace("?, ", "? ").replace("?.", "?")
    txt = txt.replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
    return txt

def write_txt(txt):
    with open("makeshift.txt", "w") as f:
        f.write(txt)

def run():
    nlp = load_spacy()
    sources = {}
    apprentice, sents = load_apprentice_sents(nlp)
    sources['apprentice'] = apprentice
    sources['sents'] = sents
    sources['kleiser'] = load_kleiser(nlp)
    sources['repub'] = load_repub(nlp)
    sources['conwell'] = load_conwell(nlp)

    txt = generate_text(sources)
    txt = clean_text(txt)
    print("{} words".format(len(txt.split())))
    write_txt(txt)

if __name__=="__main__":
    run()

