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

    def __init__(self):
        self.__repo = None

    def prepare_persistent(self, context, file_descs):
        config = context.get_config()
        git_address = config.get_necessary(constants.GIT_ADDRESS)
        branch = config.get(constants.GIT_BRANCH)
        git_branch = branch if branch else "master"
        self.__repo = Repo.clone_from(git_address, context.get_base_path(), b=git_branch)

    def post_persistent(self, context, file_descs):
        git = self.__repo.git
        git.add("*")
        git.commit('-m', ' gen code :)')
        git.push()
