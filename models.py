from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    sites = db.relationship('Site', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class Site(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pages = db.relationship('Page', backref='site', lazy=True, cascade="all, delete-orphan")
    topic_clusters = db.relationship('TopicCluster', backref='site', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Site {self.name}>'

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Page {self.url}>'

class TopicCluster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('site.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('topic_cluster.id'), nullable=True)
    children = db.relationship('TopicCluster', backref=db.backref('parent', remote_side=[id]))
    articles = db.relationship('Article', backref='topic_cluster', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<TopicCluster {self.name}>'

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    meta_description = db.Column(db.String(500), nullable=True)
    tags = db.Column(db.String(500), nullable=True)
    body_markdown = db.Column(db.Text, nullable=True)
    topic_cluster_id = db.Column(db.Integer, db.ForeignKey('topic_cluster.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f'<Article {self.title}>'
