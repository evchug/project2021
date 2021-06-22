from main import db
import datetime


class Graffiti(db.Model):
    __tablename__ = "graffiti"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='default_name')
    username = db.Column(db.String(128), default='default_name')
    email = db.Column(db.String(128), default='')
    added = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    description = db.Column(db.String(10000), default='default_text')
    address = db.Column(db.String(512), default='')
    file_name = db.Column(db.String(256), default='default_name')
    active = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return '<Graffiti %r>' % self.id
