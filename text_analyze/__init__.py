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


