from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from models import db, Site, Page, TopicCluster, Article
from auth import login_required
from crawler import crawl_site
from analysis import analyze_site_content
from article_generator import generate_article_for_cluster

site_bp = Blueprint('site', __name__, url_prefix='/site', template_folder='templates')

@site_bp.route('/add', methods=('POST',))
@login_required
def add_site():
    name = request.form['name']
    url = request.form['url']
    error = None

    if not name:
        error = 'Site name is required.'
    elif not url:
        error = 'URL is required.'

    if error is None:
        new_site = Site(name=name, url=url, user_id=g.user.id)
        db.session.add(new_site)
        db.session.commit()

        # In a production app, this should be offloaded to a background task worker (e.g., Celery, RQ)
        # to avoid blocking the web process.
        crawl_site(new_site.id, new_site.url)

        flash(f'Site "{name}" added successfully. Crawling has started.')
        return redirect(url_for('main.dashboard'))

    flash(error)
    return redirect(url_for('main.dashboard'))

@site_bp.route('/<int:site_id>')
@login_required
def view_site(site_id):
    site = db.session.get(Site, site_id)
    if site is None:
        return "Site not found", 404
    # Add logic to ensure the user owns this site
    if site.user_id != g.user.id:
        return "Access Denied", 403

    pages = Page.query.filter_by(site_id=site.id).all()
    # Fetch only top-level clusters (pillar topics)
    clusters = TopicCluster.query.filter_by(site_id=site.id, parent_id=None).all()
    return render_template('site/view_site.html', site=site, pages=pages, clusters=clusters)

@site_bp.route('/<int:site_id>/analyze', methods=('POST',))
@login_required
def trigger_analysis(site_id):
    site = db.session.get(Site, site_id)
    if site is None:
        return "Site not found", 404
    if site.user_id != g.user.id:
        return "Access Denied", 403

    # In a production app, this should be offloaded to a background task worker.
    analyze_site_content(site_id)

    flash(f"Analysis started for {site.name}. The results will appear below once complete.")
    return redirect(url_for('site.view_site', site_id=site.id))

@site_bp.route('/<int:site_id>/generate-articles', methods=('POST',))
@login_required
def generate_articles(site_id):
    site = db.session.get(Site, site_id)
    if site is None:
        return "Site not found", 404
    if site.user_id != g.user.id:
        return "Access Denied", 403

    cluster_ids = request.form.getlist('cluster_ids')
    if not cluster_ids:
        flash("You didn't select any clusters to generate articles for.", "error")
        return redirect(url_for('site.view_site', site_id=site.id))

    for cluster_id in cluster_ids:
        # In a production app, this should be offloaded to a background task worker.
        generate_article_for_cluster(cluster_id)

    flash(f"Started article generation for {len(cluster_ids)} topics. This may take some time.")
    return redirect(url_for('site.view_site', site_id=site.id))

@site_bp.route('/article/<int:article_id>')
@login_required
def view_article(article_id):
    article = db.session.get(Article, article_id)
    if article is None:
        return "Article not found", 404
    # Check if the user owns the site this article belongs to
    if article.topic_cluster.site.user_id != g.user.id:
        return "Access Denied", 403

    return render_template('site/view_article.html', article=article)
