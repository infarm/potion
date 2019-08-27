import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

from flask_potion import Api, fields
from flask_potion.contrib.alchemy import SQLAlchemyManager
from flask_potion.resource import ModelResource

from . import ApiClient


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = 'XXX'
    app.test_client_class = ApiClient
    app.debug = True
    return app


@pytest.fixture
def api(app):
    return Api(app, default_manager=SQLAlchemyManager)


@pytest.fixture
def sa(app):
    app.config['SQLALCHEMY_ENGINE'] = 'sqlite://'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
    return SQLAlchemy(app, session_options={"autoflush": False})


@pytest.fixture
def Machine(sa, api, Type):
    class Machine(sa.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(60), nullable=False)

        wattage = sa.Column(sa.Float)

        type_id = sa.Column(sa.Integer, sa.ForeignKey(Type.id))
        type = sa.relationship(
            Type, backref=backref('machines', lazy='dynamic', uselist=True)
        )

    return Machine


@pytest.fixture
def Type(sa, api):
    class Type(sa.Model):
        id = sa.Column(sa.Integer, primary_key=True)
        name = sa.Column(sa.String(60), nullable=False, unique=True)
        version = sa.Column(sa.Integer(), nullable=True)

    return Type


@pytest.fixture
def db(Type, Machine, sa):
    sa.create_all()
    yield sa
    sa.drop_all()


@pytest.fixture
def resources(Type, Machine, api):
    class MachineResource(ModelResource):
        class Meta:
            model = Machine
            include_id = True
            include_type = True

        class Schema:
            type = fields.ToOne('type')

    class TypeResource(ModelResource):
        class Meta:
            model = Type
            include_id = True
            include_type = True

        class Schema:
            machines = fields.ToMany('machine')

    api.add_resource(MachineResource)
    api.add_resource(TypeResource)
    return Type, Machine


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client
