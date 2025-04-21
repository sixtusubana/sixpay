"""Flask config."""
import os
from os import environ, path
from dotenv import load_dotenv
from API.settings import *

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


class Config:
    """Base config."""
    SECRET_KEY = os.getenv("SECRET_KEY") or 'JDJNSVJNVJFVJFJJJJJJJVNNVNJFJVNDVNDJVNJDNJVDJ'
    JWT_SECRET_KEY = os.getenv("SECRET_KEY") or 'JDJNSVJNVJFVJFJJJJJJJVNNVNJFJVNDVNDJVNJDNJVDJ'
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'





class DevConfig(Config):
    FLASK_ENV = 'development'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sixpay.db'
   