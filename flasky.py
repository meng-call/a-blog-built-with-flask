import os
import sys
import click
from app import create_app, db
from app.models import User, Role, Post
from flask_migrate import Migrate

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Post=Post)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False, help='Run tests under code coverage.')
def test(coverage):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(os.execvp(sys.executable, [sys.executable] + ['-m', 'flask', 'test', '--coverage']))
    import unittest
    tests = unittest.TestLoader().discover('test')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()


@app.cli.command()
@click.option('--count', default=100, help='Number of users to generate.')
def forge_users(count):
    """Generate fake users."""
    from sqlalchemy.exc import IntegrityError
    from faker import Faker
    
    fake = Faker()
    i = 0
    while i < count:
        u = User(
            email=fake.email(),
            username=fake.user_name(),
            password='password',
            confirmed=True,
            name=fake.name(),
            location=fake.city(),
            about_me=fake.text(),
            member_since=fake.past_date()
        )
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


@app.cli.command()
@click.option('--count', default=100, help='Number of posts to generate.')
def forge_posts(count):
    """Generate fake posts."""
    from random import randint
    from faker import Faker
    
    fake = Faker()
    user_count = User.query.count()
    
    if user_count == 0:
        print("No users found. Please run 'flask forge-users' first.")
        return
    
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(
            body=fake.text(),
            timestamp=fake.past_date(),
            author=u
        )
        db.session.add(p)
    
    db.session.commit()
    print(f"Generated {count} posts.")

