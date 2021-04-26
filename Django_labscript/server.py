from waitress import serve

from dj_ls_project.wsgi import application

from waitress import logging


if __name__ == '__main__':
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    serve(application,  listen="129.206.182.92:8000 localhost:8000")#, port='8000', host='129.206.182.92'
