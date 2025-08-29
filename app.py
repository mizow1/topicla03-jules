import os
from flask import Flask
from models import db
import markdown

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # Configure the database
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'your_super_secret_key_for_dev'),
        SQLALCHEMY_DATABASE_URI='sqlite:///site.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Enable debug mode and logging
    app.config['DEBUG'] = True
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Ensure the instance folder exists - no longer needed as we are not using it for the db
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # Initialize the database
    db.init_app(app)

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    import main
    app.register_blueprint(main.main_bp)

    from site_views import site_bp
    app.register_blueprint(site_bp)

    # Command to create database tables
    @app.cli.command('init-db')
    def init_db_command():
        """Creates the database tables."""
        with app.app_context():
            db.create_all()
        print('Initialized the database.')

    # Register Markdown filter
    @app.template_filter('markdown')
    def markdown_filter(s):
        return markdown.markdown(s)

    return app

app = create_app()

if __name__ == '__main__':
    try:
        print("サーバーを起動しています...")
        print("URL: http://localhost:3000")
        app.run(debug=True, host='localhost', port=3000, threaded=True)
    except Exception as e:
        print(f"サーバー起動エラー: {e}")
        print("代替ポートで再試行...")
        app.run(debug=True, host='localhost', port=0, threaded=True)
