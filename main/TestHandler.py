from main.process.makers import *
from main.support.specific import DbApplicationContext, ParallelGitDelivery
from main.utis import constants
from main.utis.utils import Configuration

context = DbApplicationContext(Configuration.from_dic({
    constants.APP_NAME: "test-service",
    constants.IS_CREATE_NEW: True,
    constants.IS_MODULARIZATION_PROJECT: True,
    constants.DB: {
        "host": "192.168.1.54",
        "port": 3306,
        "user_name": "dev-all",
        "password": "all201705",
        "database": "test",
        "tables": [
            "complete",
            "complete2"
        ]
    },
    constants.GIT_ADDRESS: "git@git.wanshifu.com:jirenhe/test-service.git",
    constants.GIT_BRANCH: "new_1",
    constants.API_BASE_PACKAGE: "com.wanshifu.test",
    constants.DAO_PACKAGE: "com.wanshifu.mapper",
    constants.PO_PACKAGE: "com.wanshifu.test.domain.po",
    constants.MAPPER_XML_PACKAGE: "mappers",
    constants.WITH_DATABASE: True,
    constants.WITH_MQ: True,
    constants.WITH_REDIS: True,
}))


def do_test(l):
    for h in l:
        h.make(context)
    for f in context.get_file_descs():
        print(f.file_content)
    ParallelGitDelivery().delivery(context)


def main():
    l = [MybaitisDaoMaker(), MybaitisPoMaker(), MybaitisXmlMaker(), PomXmlMaker(), ApplicationClassMaker(),
         LogbackXmlMaker(), ConfigPropertiesMaker(), H2CreateTableSqlMaker(), ApiAutoConfigMaker()]
    do_test(l)


if __name__ == "__main__":
    main()
