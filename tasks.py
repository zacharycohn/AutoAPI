import glob
import logging

import sqlalchemy as sa
from invoke import run, task

import app
import aws
import config
import refresh_log
import utils
from refresh_log import AutoapiTableRefreshLog as RefreshLog

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@task
def requirements(ctx, upgrade=True):
    cmd = 'pip install -r requirements.txt'
    if upgrade:
        cmd += ' --upgrade'
    run(cmd)


@task
def apify(ctx, filename, tablename=None):
    try:
        filenames = glob.glob(filename, recursive=True)
    except TypeError:  # recursive glob in Python 3.5+ only
        filenames = glob.glob(filename)
    if len(filenames) > 1 and tablename:
        raise Exception("Can't specify a `tablename` for >1 file")
    for filename in filenames:
        _tablename = tablename or utils.get_name(filename)
        logger.info('Importing {0} to table {1}'.format(filename, _tablename))
        try:
            utils.drop_table(_tablename)
        except sa.exc.OperationalError as e:
            logger.debug('DROP TABLE {} failed, may not exist?'.format(
                _tablename))
            logger.debug(str(e))
        try:
            utils.load_table(filename, _tablename)
        except Exception as e:
            logger.error('Failed to load table from file {}'.format(filename))
            logger.error(str(e))
        utils.index_table(_tablename, config.CASE_INSENSITIVE)
        logger.info('Finished importing {0}'.format(filename))


@task
def delete_from_bucket(ctx, filename, bucket_name=None):
    aws.delete_from_bucket(filename, bucket_name)


@task
def copy_to_bucket(ctx, filename, bucket_name=None):
    aws.copy_to_bucket(filename, bucket_name)


@task
def list_bucket(ctx, bucket_name=None):
    aws.list_bucket(bucket_name)


@task
def fetch_bucket(ctx, bucket_name=None):
    aws.fetch_bucket(bucket_name)


@task
def serve(ctx):
    app.make_app().run(host='0.0.0.0')


@task
def refresh(ctx, clear_tables=True):
    logger.info('Refresh invoked')
    with app.make_app().app_context():
        rlog_id = RefreshLog.start()
        logger.info('refresh log id {} started'.format(rlog_id))
        try:
            aws.fetch_bucket(clear_tables=clear_tables)
            logger.debug('bucket fetched')
            utils.refresh_tables()
            logger.info('refresh complete')
            refresh_log.stop(rlog_id)
        except Exception as e:
            refresh_log.stop(rlog_id, err_msg=str(e))


@task
def quick_refresh(ctx):
    refresh(clear_tables=False)


@task
def clear(ctx):
    utils.clear_tables()
