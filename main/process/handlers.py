import os
import re

from jinja2 import Environment, PackageLoader
from jinja2 import Template

import main.utis.constants as constants
from main.support.abstract import Handler, ABCMeta, abstractmethod, AbstractBaseEachTableHandler, \
    AbstractDbApplicationContext
from main.support.exception import IllegalArgumentError
from main.utis.utils import FileDesc, under_line2_camel, package_to_path, none_replace_format

env = Environment(loader=PackageLoader("main.process"))


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


class AbstractSimpleTemplatesHandler(Handler, metaclass=ABCMeta):

    def hand(self, context):
        per_render_file_descs = self.get_pre_file_descs(context)
        d = self.ext_render_para(context)
        if d is None:
            d = {}
        render_para = dict(d, **context.get_config().root)
        for f in per_render_file_descs:
            assert isinstance(f, PreRenderFileDesc)
            context.append_file_desc(FileDesc(f.name, f.path, f.tmp.render(render_para)))

    @abstractmethod
    def get_pre_file_descs(self, context):
        pass

    def ext_render_para(self, context):
        return dict({}, **context.get_config().root)


class PomXmlHandler(AbstractSimpleTemplatesHandler):

    def get_pre_file_descs(self, context):
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


class ApplicationClassHandler(AbstractSimpleTemplatesHandler):

    def __init__(self):
        self.app_class_name = None

    def get_pre_file_descs(self, context):
        app_class_name = self.__get_app_class_name(context)
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
            app_class_name=self.__get_app_class_name(context)
        )

    def __get_app_class_name(self, context):
        if self.app_class_name is None:
            app_class_name = under_line2_camel(context.app_name, '-')
            self.app_class_name = app_class_name[:1].upper() + app_class_name[1:]
        return self.app_class_name


class LogbackXmlHandler(AbstractSimpleTemplatesHandler):

    def get_pre_file_descs(self, context):
        return [
            PreRenderFileDesc("logback-spring.xml", context.get_web_resources_path(),
                              constants.TEMPLATE_LOG_BACK_XML),
            PreRenderFileDesc("logback-spring.xml", context.get_web_test_resource_path(),
                              constants.TEMPLATE_LOG_BACK_TEST_XML)
        ]


class ConfigPropertiesHandler(AbstractSimpleTemplatesHandler):

    def get_pre_file_descs(self, context):
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


class MybaitisDaoGen(AbstractBaseEachTableHandler):

    def resolve_file_name(self, context, table):
        return table.java_class_name + "Mapper.java"

    def resolve_file_path(self, context, table):
        return package_to_path(context.get_config().get(constants.DAO_PACKAGE), context.get_web_java_path())

    def get_template(self):
        return env.get_template(constants.TEMPLATE_MAPPER)


class MybaitisPoGen(AbstractBaseEachTableHandler):

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


class MybaitisXmlGen(AbstractBaseEachTableHandler):

    def resolve_file_name(self, context, table):
        return table.java_class_name + ".xml"

    def resolve_file_path(self, context, table):
        return package_to_path(context.get_config().get(constants.MAPPER_XML_PACKAGE), context.get_web_resources_path())

    def get_template(self):
        return env.get_template(constants.TEMPLATE_MAPPER_XML)


class H2CreateTableSqlHandler(Handler):
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

    def hand(self, context):
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
