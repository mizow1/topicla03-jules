from flask import Blueprint, render_template, g
from auth import login_required

main_bp = Blueprint('main', __name__, template_folder='templates')

@main_bp.route('/')
def index():
    return render_template('main/index.html', user=g.user)

from models import Site

@main_bp.route('/dashboard')
@login_required
def dashboard():
    sites = Site.query.filter_by(user_id=g.user.id).all()
    return render_template('main/dashboard.html', user=g.user, sites=sites)
