from flask import Blueprint, render_template, session
import tagme
import json
from database import db
from general import TopArtists
from text_analyze import Event, EventWiki, WikiContent, tagme_annotation


spotify_tagme_bp = Blueprint('spotify_tagme_bp', __name__)

keys_tagme = {"token": ""}

try:
    keys_tagme = json.load(open('keys_tagme.json', 'r'))
except Exception as e:
    print(e)

tagme.GCUBE_TOKEN = str(keys_tagme["token"])


@spotify_tagme_bp.route('/load_event')
def load_artist():
    path = '/Users/yuliang/Desktop/text_for_novmusic/event.json'

    with open(path) as json_file:
        events = json.load(json_file)['events']

    for event in events:
        event_obj = Event(name=event["name"], info=event["info"], url=event["url"])
        db.session.add(event_obj)
    db.session.commit()

    return render_template("test.html")


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


