#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role, Vendor, Merchant, Listing, Category
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand
from config import Config

# Import settings from .env file. Must define FLASK_CONFIG
if os.path.exists('.env'):
    print('Importing environment from .env file')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def setup_test_vendor_merchant():
    u1 = Merchant(
        first_name="Merch",
        last_name="Ant",
        email="merchant@example.com",
        password="password",
        company_name="Hunter's Diner",
        confirmed=True,
        role=Role.query.filter_by(index='merchant').first(),
    )
    u2 = Vendor(
        first_name="Ven",
        last_name="Dor",
        email="vendor@example.com",
        password="password",
        company_name="Jonny's Bagels",
        confirmed=True,
        role=Role.query.filter_by(index='vendor').first(),
    )
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()


@manager.command
def setup_test_listings():
    c = Category(name="Milk", unit="Gallons")
    db.session.add(c)
    u1 = Listing(
        vendor_id=Vendor.query.filter_by(first_name="Ven").first().id,
        category_id=Category.query.filter_by(name="Milk").first().id,
        name="Broccoli",
        description="Best Broccoli Around",
        price=5.00,
        available=True
    )
    u2 = Listing(
        vendor_id=Vendor.query.filter_by(first_name="Ven").first().id,
        category_id=Category.query.filter_by(name="Milk").first().id,
        name="Eggs",
        description="Best Eggs Around",
        price=12.00,
        available=True
    )
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()
    setup_default_user()
    setup_test_vendor_merchant()
    setup_test_listings()


@manager.command
def setup_default_user():
    """
    Sets up a default user as the admin
    """
    # Roles have to be set up for this to work, so we set them up
    # when this is called. Won't have negative side effects if
    # roles are already set up
    Role.insert_roles()

    c = Config()
    admin_role = Role.query.filter_by(index='admin').first()
    user = User(role=admin_role,
                email=c.DEFAULT_EMAIL,
                first_name=c.DEFAULT_FIRST,
                last_name=c.DEFAULT_LAST,
                password=c.DEFAULT_PASSWORD,
                confirmed=True)
    db.session.add(user)
    db.session.commit()


@manager.option('-n',
                '--number-users',
                default=10,
                type=int,
                help='Number of each model type to create',
                dest='number_users')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)


@manager.command
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()


@manager.command
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production."""
    pass

if __name__ == '__main__':
    manager.run()
