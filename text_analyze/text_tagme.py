from flask import Blueprint, render_template
import tagme
import json

tagme_bp = Blueprint('tagme_bp', __name__)

keys_tagme = {"token": ""}

try:
    keys_tagme = json.load(open('keys_tagme.json', 'r'))
except Exception as e:
    print(e)

tagme.GCUBE_TOKEN = str(keys_tagme["token"])


def tagme_rel(wid_pairs):
    rels = tagme.relatedness_title(wid_pairs)

    return rels.relatedness


def tagme_annotation(text_to_annotate):
    event = tagme.annotate(text_to_annotate)

    dict_ann = {}

    # Print annotations with a score higher than 0.3
    for ann in event.get_annotations(0.3):
        dict_ann[str(ann.entity_id)] = ann.entity_title

    return dict_ann
