from waitress import serve

from dj_ls_project.wsgi import application

from waitress import logging


if __name__ == '__main__':
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    serve(application,  listen="XX.XX.XX.XX:8000 localhost:8000")
