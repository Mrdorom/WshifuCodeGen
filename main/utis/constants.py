import os

WORK_SPACE = "{}gen_work_space{}".format(os.path.abspath('..') + os.sep, os.sep)
APP_NAME = "app_name"
IS_MODULARIZATION_PROJECT = "is_modularization_project"
WITH_DATABASE = "with_database"
WITH_MQ = "with_mq"
WITH_REDIS = "with_redis"
IS_CREATE_NEW = "is_create_new"
GIT_ADDRESS = "git_address"
GIT_BRANCH = "git_branch"
DB = "db"
DB_HOST = "db.host"
DB_PORT = "db.port"
DB_USER_NAME = "db.user_name"
DB_PASSWORD = "db.password"
DB_DATABASE = "db.database"
DB_TABLES = "db.tables"
DAO_PACKAGE = "dao_package"
PO_PACKAGE = "po_package"
MAPPER_XML_PACKAGE = "mapper_xml_package"
TEMPLATE_MAPPER = "MapperTemplate.java"
TEMPLATE_PO = "PoTemplate.java"
TEMPLATE_MAPPER_XML = "MapperXmlTemplate.xml"
TEMPLATE_MODULARIZATION_PARENT_POM = "modularization/ParentPom.xml"
TEMPLATE_MODULARIZATION_WEB_POM = "modularization/WebModulePom.xml"
TEMPLATE_MODULARIZATION_API_POM = "modularization/ApiModulePom.xml"
TEMPLATE_SINGLEMODULE_POM = "singlemodule/SinglePom.xml"
TEMPLATE_APPLICATION_CLASS = "Application.java"
TEMPLATE_APPLICATION_TEST_CLASS = "AppTest.groovy"
TEMPLATE_LOG_BACK_XML = "logback-spring.xml"
TEMPLATE_LOG_BACK_TEST_XML = "logback-spring-test.xml"
TEMPLATE_CONFIG_PROPERTIES = "application.properties"
TEMPLATE_CONFIG_PROPERTIES_LOCAL = "application-local.properties"
TEMPLATE_CONFIG_PROPERTIES_DEV = "application-dev.properties"
TEMPLATE_CONFIG_PROPERTIES_TEST = "application-test.properties"
TEMPLATE_CONFIG_PROPERTIES_PROD = "application-prod.properties"
TEMPLATE_CONFIG_PROPERTIES_TEST_CASE = "application-test-case.properties"
CURRENT_FRAME_WORK_VERSION = "1.0.4"
CURRENT_MICROSERVICE_PARENT_VERSION = "1.0.1"
