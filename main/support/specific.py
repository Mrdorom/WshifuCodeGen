import pymysql
from git import Repo

import main.support.mysql as mysql
import main.utis.constants as constants
from main.support.abstract import AbstractDbApplicationContext, AbstractParallelDelivery


class DbApplicationContext(AbstractDbApplicationContext):

    def __init__(self, config):
        super().__init__(config)
        di = dict(
            host=config.get_necessary(constants.DB_HOST),
            user=config.get_necessary(constants.DB_USER_NAME),
            password=config.get_necessary(constants.DB_PASSWORD),
            database=config.get_necessary(constants.DB_DATABASE),
            port=config.get_necessary(constants.DB_PORT),
        )
        self.specific_tables = config.get_list(constants.DB_TABLES)
        self.__connect_detail = di
        self.__init_tables()

    def create_db_connect(self):
        return pymysql.connect(**self.__connect_detail)

    def get_tables(self):
        return self.__tables

    def __init_tables(self):
        con = self.create_db_connect()
        cursor = con.cursor()
        self.__tables = mysql.get_tables(cursor, self.__connect_detail['database'], *self.specific_tables)
        cursor.close()
        con.close()


class ParallelGitDelivery(AbstractParallelDelivery):
    context_key = "ParallelGit"

    def prepare_persistent(self, context, file_descs):
        config = context.get_config()
        git_address = config.get_necessary(constants.GIT_ADDRESS)
        branch = config.get(constants.GIT_BRANCH)
        git_branch = branch if branch else "master"
        repo = Repo.clone_from(git_address, context.get_base_path())
        git = repo.git
        remote_exist = True
        try:
            git.checkout(git_branch)
        except:
            remote_exist = False
            git.checkout('-b', git_branch)
        if remote_exist:
            git.pull()
        context.custom_context(self.context_key, dict(
            repo=repo,
            git=git,
            git_branch=git_branch,
            remote_exist=remote_exist
        ))

    def post_persistent(self, context, file_descs):
        local_context = context.custom_context(self.context_key)
        git = local_context['git']
        remote_exist = local_context['remote_exist']
        if remote_exist:
            git.pull()
        git.add("*")
        git.commit('-m', ' gen code :)')
        git.push('-u', 'origin', local_context['git_branch'])
