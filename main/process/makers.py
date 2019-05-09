import os
import re

from jinja2 import Environment, PackageLoader
from jinja2 import Template

import main.utis.constants as constants
from main.support.abstract import FileMaker, ABCMeta, abstractmethod, AbstractBaseEachTableFileMaker, \
    AbstractDbApplicationContext
from main.support.exception import IllegalArgumentError
from main.utis.utils import FileDesc, under_line2_camel, package_to_path, none_replace_format

env = Environment(loader=PackageLoader("main.process"))


class AppClassNameAware:

    def get_app_class_name(self, context):
        app_class_name = under_line2_camel(context.app_name, '-')
        app_class_name = app_class_name[:1].upper() + app_class_name[1:]
        return app_class_name


class PreRenderFileDesc:

    def __init__(self, name, path, tmp):
        assert name
        assert path
        self.name = name
        self.path = path
        if isinstance(tmp, Template):
            self.tmp = tmp
        elif isinstance(tmp, str):
            self.tmp = env.get_template(tmp)
        else:
            raise IllegalArgumentError()


class AbstractSimpleTemplatesFileMaker(FileMaker, metaclass=ABCMeta):

    def make(self, context):
        d = self.ext_render_para(context)
        if d is None:
            d = {}
        per_render_file_descs = self.get_pre_file_descs(context, d)
        render_para = dict(d, **context.get_config().root)
        for f in per_render_file_descs:
            assert isinstance(f, PreRenderFileDesc)
            context.append_file_desc(FileDesc(f.name, f.path, f.tmp.render(render_para)))

    @abstractmethod
    def get_pre_file_descs(self, context, d):
        pass

    def ext_render_para(self, context):
        return dict({}, **context.get_config().root)


class PomXmlMaker(AbstractSimpleTemplatesFileMaker):

    def get_pre_file_descs(self, context, para):
        if context.is_modularization_project():
            return [
                PreRenderFileDesc("pom.xml", context.get_base_path(), constants.TEMPLATE_MODULARIZATION_PARENT_POM),
                PreRenderFileDesc("pom.xml", context.get_api_path(), constants.TEMPLATE_MODULARIZATION_API_POM),
                PreRenderFileDesc("pom.xml", context.get_web_path(), constants.TEMPLATE_MODULARIZATION_WEB_POM),
            ]
        else:
            return [
                PreRenderFileDesc("pom.xml", context.get_base_path(), constants.TEMPLATE_SINGLEMODULE_POM),
            ]

    def ext_render_para(self, context):
        return dict(
            microservice_parent_version=constants.CURRENT_MICROSERVICE_PARENT_VERSION,
            framework_version=constants.CURRENT_FRAME_WORK_VERSION,
        )


class ApplicationClassMaker(AbstractSimpleTemplatesFileMaker, AppClassNameAware):

    def get_pre_file_descs(self, context, para):
        app_class_name = para['app_class_name']
        return [
            PreRenderFileDesc(app_class_name + "Application.java",
                              package_to_path("com.wanshifu", context.get_web_java_path()),
                              constants.TEMPLATE_APPLICATION_CLASS),
            PreRenderFileDesc(app_class_name + "AppTest.groovy",
                              package_to_path("com.wanshifu", context.get_web_test_groovy_path()),
                              constants.TEMPLATE_APPLICATION_TEST_CLASS)
        ]

    def ext_render_para(self, context):
        return dict(
            app_class_name=self.get_app_class_name(context)
        )


class LogbackXmlMaker(AbstractSimpleTemplatesFileMaker):

    def get_pre_file_descs(self, context, para):
        return [
            PreRenderFileDesc("logback-spring.xml", context.get_web_resources_path(),
                              constants.TEMPLATE_LOG_BACK_XML),
            PreRenderFileDesc("logback-spring.xml", context.get_web_test_resource_path(),
                              constants.TEMPLATE_LOG_BACK_TEST_XML)
        ]


class ConfigPropertiesMaker(AbstractSimpleTemplatesFileMaker):

    def get_pre_file_descs(self, context, para):
        s = os.sep
        return [
            PreRenderFileDesc("application.properties", context.get_web_resources_path() + s + "config" + s,
                              constants.TEMPLATE_CONFIG_PROPERTIES),
            PreRenderFileDesc("application-local.properties", context.get_web_resources_path() + s + "config" + s,
                              constants.TEMPLATE_CONFIG_PROPERTIES_LOCAL),
            PreRenderFileDesc("application-dev.properties", context.get_web_resources_path() + s + "config" + s,
                              constants.TEMPLATE_CONFIG_PROPERTIES_DEV),
            PreRenderFileDesc("application-test.properties", context.get_web_resources_path() + s + "config" + s,
                              constants.TEMPLATE_CONFIG_PROPERTIES_TEST),
            PreRenderFileDesc("application-prod.properties", context.get_web_resources_path() + s + "config" + s,
                              constants.TEMPLATE_CONFIG_PROPERTIES_PROD),
            PreRenderFileDesc("application-test-case.properties",
                              context.get_web_test_resource_path() + s + "config" + s,
                              constants.TEMPLATE_CONFIG_PROPERTIES_TEST_CASE),
        ]


class MybaitisDaoMaker(AbstractBaseEachTableFileMaker):

    def resolve_file_name(self, context, table):
        return table.java_class_name + "Mapper.java"

    def resolve_file_path(self, context, table):
        return package_to_path(context.get_config().get(constants.DAO_PACKAGE), context.get_web_java_path())

    def get_template(self):
        return env.get_template(constants.TEMPLATE_MAPPER)


class MybaitisPoMaker(AbstractBaseEachTableFileMaker):

    def render_para(self, context, table):
        import_info = table.import_set.copy()
        import_info.add("javax.persistence.*")
        import_info.add("lombok.Data")
        import_info.add("lombok.ToString")
        for f in table.fields:
            f.annotations = []
            if f.is_pk:
                f.annotations.append("@Id")
                if f.is_auto_increment:
                    f.annotations.append("@GeneratedValue(strategy = GenerationType.IDENTITY)")
            f.annotations.append("@Column(name = \"{}\")".format(f.meta_data['column_name']))
        return dict(dict(import_info=import_info), **dict(table.__dict__, **context.get_config().root))

    def resolve_file_name(self, context, table):
        return table.java_class_name + ".java"

    def resolve_file_path(self, context, table):
        return package_to_path(context.get_config().get(constants.PO_PACKAGE),
                               context.get_api_java_path()
                               if context.is_modularization_project()
                               else context.get_web_java_path())

    def get_template(self):
        return env.get_template(constants.TEMPLATE_PO)


class MybaitisXmlMaker(AbstractBaseEachTableFileMaker):

    def resolve_file_name(self, context, table):
        return table.java_class_name + ".xml"

    def resolve_file_path(self, context, table):
        return package_to_path(context.get_config().get(constants.MAPPER_XML_PACKAGE), context.get_web_resources_path())

    def get_template(self):
        return env.get_template(constants.TEMPLATE_MAPPER_XML)


class H2CreateTableSqlMaker(FileMaker):
    replaces = [
        {
            "pattern": re.compile(r"ENGINE=InnoDB(\sAUTO_INCREMENT=\d+)? (DEFAULT CHARSET=\S+)?\s?(COMMENT='.*')?(;)?"),
            "lambada": lambda x: none_replace_format("{}{};", x.group(3), x.group(4))
        },
        {
            "pattern": re.compile(r"\s*ON UPDATE CURRENT_TIMESTAMP"),
            "lambada": ""
        },
        {
            "pattern": re.compile(r"KEY(\s\S+\s)\s?(\(\S+\))\s?(USING BTREE)?(,)?\n?"),
            "lambada": lambda x: none_replace_format("KEY {} {}\n", x.group(2), x.group(4))
        },
        {
            "pattern": re.compile(r",\n\s*(?<!UNIQUE)(?<!PRIMARY)\s?KEY\s+\(\S+\)"),
            "lambada": ""
        },
        {
            "pattern": re.compile(r"CHARACTER SET\s\S+\s"),
            "lambada": ""
        },
        {
            "pattern": re.compile(r"(double|float)\((\d+),\d?\)"),
            "lambada": lambda x: none_replace_format("{}({})", x.group(1), x.group(2))
        },
        {
            "pattern": re.compile(r"` (enum|set)\(.*\)"),
            "lambada": "` varchar(255)"
        },
    ]

    def make(self, context):
        assert isinstance(context, AbstractDbApplicationContext)
        con = context.create_db_connect()
        cursor = con.cursor()
        file_content = ""
        for table in context.get_tables():
            cursor.execute("SHOW CREATE TABLE {}".format(table.meta_data['name']))
            row = cursor.fetchone()
            if row:
                file_content += "DROP TABLE IF EXISTS {}; \n\n".format(table.meta_data['name'])
                s = row[1]
                for replace in self.replaces:
                    s = re.sub(replace['pattern'], replace['lambada'], s)
                s += "\n" * 3
                file_content += s
        cursor.close()
        con.close()
        context.append_file_desc(
            FileDesc("createTable.sql", context.get_web_test_resource_path() + os.sep + "sql" + os.sep, file_content))


class ApiAutoConfigMaker(AbstractSimpleTemplatesFileMaker, AppClassNameAware):

    def ext_render_para(self, context):
        d = super().ext_render_para(context)
        app_class_name = self.get_app_class_name(context)
        config = context.get_config()
        base_package = config.get_necessary(constants.API_BASE_PACKAGE)
        project_host = config.get(constants.PROJECT_HOST)
        project_host = project_host if project_host else config.get('app_name') + ".wanshifu.com"
        class_full_name = base_package + "." + app_class_name
        while class_full_name.__contains__(".."):
            class_full_name = class_full_name.replace("..", ".")
        return dict(d, app_class_name=app_class_name, class_full_name=class_full_name, project_host=project_host,
                    base_package=base_package)

    def get_pre_file_descs(self, context, para):
        s = os.sep
        app_class_name = para['app_class_name']
        base_package = para['base_package']
        return [
            PreRenderFileDesc(app_class_name + "ApiConfiguration",
                              package_to_path(base_package, context.get_api_java_path()),
                              constants.TEMPLATE_API_CONFIGURATION_CLASS),
            PreRenderFileDesc("spring.factories", context.get_api_resources_path() + s + "META-INF" + s,
                              constants.TEMPLATE_SPRING_FACTORIES),
        ]
