from flask import Blueprint, render_template, session
import json
from general import TopArtists
from database import db
import tagme


class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
    name = db.Column(db.VARCHAR)
    info = db.Column(db.VARCHAR)
    url = db.Column(db.VARCHAR)
    eventWiki = db.relationship('EventWiki', cascade='all')

    def __repr__(self):
        return '<Event %r>' % self.id


class EventWiki(db.Model):
    __tablename = 'event_wiki'
    event_id = db.Column(db.INTEGER, db.ForeignKey('event.id'), primary_key=True)
    wiki_id = db.Column(db.INTEGER, db.ForeignKey('wiki_content.id'), primary_key=True)
    wikiContent = db.relationship('WikiContent', cascade='save-update, merge')

    def __repr__(self):
        return '<EventWiki %r-%r>' % (self.event_id, self.wiki_id)


class WikiContent(db.Model):
    __tablename = 'wiki_content'
    id = db.Column(db.INTEGER, primary_key=True)
    title = db.Column(db.VARCHAR)

    def __repr__(self):
        return '<WikiContent %r>' % self.id


spotify_tagme_bp = Blueprint('spotify_tagme_bp', __name__)

keys_tagme = {"token": ""}

try:
    keys_tagme = json.load(open('keys_tagme.json', 'r'))
except Exception as e:
    print(e)

tagme.GCUBE_TOKEN = str(keys_tagme["token"])


@spotify_tagme_bp.route('/annote_event')
def annote_event():
    events = db.session.query(Event).all()

    for event in events:
        dict_ann = tagme_annotation(event.info)

        try:
            for ann in dict_ann:
                wiki_content_obj = WikiContent.query.filter_by(id=ann).first()
                if wiki_content_obj:
                    event_wiki_obj = EventWiki(event_id=event.id, wiki_id=ann, wikiContent=wiki_content_obj)
                    db.session.add(event_wiki_obj)
                else:
                    wiki_content = WikiContent(id=int(ann), title=dict_ann[ann])
                    event_wiki_obj = EventWiki(event_id=event.id, wiki_id=int(ann), wikiContent=wiki_content)
                    db.session.add(event_wiki_obj)
            db.session.commit()
        except Exception as e:
            print(e)

    return render_template('test.html')


class UserTopArtistWikiRecord(db.Model):
    __tablename = 'user_top_artist_wiki_record'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    annote_wid = db.Column(db.VARCHAR)
    annote_title = db.Column(db.VARCHAR)


@spotify_tagme_bp.route('/annote_user_top_artist')
def annote_user_top_artist():
    user_id = session["userid"]

    user_top_artist_wiki_record = UserTopArtistWikiRecord.query.filter_by(user_id=user_id).first()

    if not user_top_artist_wiki_record:
        top_artists = db.session.query(TopArtists).filter_by(user_id=user_id).group_by(TopArtists.artist_id).all()

        l_artist = []

        for artist in top_artists:
            l_artist.append(artist.artist.name)

        str_artist = ", ".join(l_artist)

        try:
            dict_ann = tagme_annotation(str_artist)

            if len(dict_ann) != 0:
                user_top_artist_wiki_record = UserTopArtistWikiRecord(user_id=user_id,
                                                                      annote_wid=";".join(list(dict_ann)),
                                                                      annote_title=";".join(list(dict_ann.values())))
                db.session.add(user_top_artist_wiki_record)
                db.session.commit()

        except Exception as e:
            print(e)

    return render_template("test.html")


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

