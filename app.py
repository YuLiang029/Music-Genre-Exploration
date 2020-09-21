from flask import Flask
from general.general import general_bp, TopArtists
from text_analyze.text_tagme import tagme_bp, tagme_annotation, tagme_rel
from database import db
from flask import session, render_template

import os
import json


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


class UserTopArtistWikiRecord(db.Model):
    __tablename = 'user_top_artist_wiki_record'
    user_id = db.Column(db.VARCHAR, db.ForeignKey('user.id'), primary_key=True)
    annote_wid = db.Column(db.VARCHAR)
    annote_title = db.Column(db.VARCHAR)


app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)
app.register_blueprint(general_bp)
app.register_blueprint(tagme_bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5001)), debug=True)


@app.route('/load_event')
def load_artist():
    path = '/Users/yuliang/Desktop/text_for_novmusic/event.json'

    with open(path) as json_file:
        events = json.load(json_file)['events']

    for event in events:
        event_obj = Event(name=event["name"], info=event["info"], url=event["url"])
        db.session.add(event_obj)
    db.session.commit()

    return render_template("test.html")


@app.route('/annote_event')
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


@app.route('/annote_user_top_artist')
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


@app.after_request
def add_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return response


