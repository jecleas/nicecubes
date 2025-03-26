import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://username:password@nice-cubes-db.xxxxx.region.rds.amazonaws.com:5432/nice_cubes'
    SQLALCHEMY_TRACK_MODIFICATIONS = False