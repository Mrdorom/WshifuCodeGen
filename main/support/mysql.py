from enum import Enum

from utis.utils import under_line2_camel


class JdbcType(Enum):
    INT = {"jdbc_type": "INTEGER", "java_type": "Integer", "java_package": "java.lang"}
    TINYINT = {"jdbc_type": "TINYINT", "java_type": "Integer", "java_package": "java.lang"}
    SMALLINT = {"jdbc_type": "SMALLINT", "java_type": "Integer", "java_package": "java.lang"}
    MEDIUMINT = {"jdbc_type": "INTEGER", "java_type": "Integer", "java_package": "java.lang"}
    BIGINT = {"jdbc_type": "BIGINT", "java_type": "Long", "java_package": "java.lang"}
    BIT = {"jdbc_type": "BIT", "java_type": "Integer", "java_package": "java.lang"}
    DOUBLE = {"jdbc_type": "DOUBLE", "java_type": "BigDecimal", "java_package": "java.math"}
    FLOAT = {"jdbc_type": "REAL", "java_type": "BigDecimal", "java_package": "java.math"}
    DECIMAL = {"jdbc_type": "DECIMAL", "java_type": "BigDecimal", "java_package": "java.math"}
    CHAR = {"jdbc_type": "CHAR", "java_type": "String", "java_package": "java.lang"}
    VARCHAR = {"jdbc_type": "VARCHAR", "java_type": "String", "java_package": "java.lang"}
    ENUM = {"jdbc_type": "CHAR", "java_type": "String", "java_package": "java.lang"}
    SET = {"jdbc_type": "CHAR", "java_type": "String", "java_package": "java.lang"}
    TINYTEXT = {"jdbc_type": "LONGVARCHAR", "java_type": "String", "java_package": "java.lang"}
    LONGTEXT = {"jdbc_type": "LONGVARCHAR", "java_type": "String", "java_package": "java.lang"}
    MEDIUMTEXT = {"jdbc_type": "LONGVARCHAR", "java_type": "String", "java_package": "java.lang"}
    DATE = {"jdbc_type": "DATE", "java_type": "Date", "java_package": "java.util"}
    DATETIME = {"jdbc_type": "TIMESTAMP", "java_type": "Date", "java_package": "java.util"}
    TIME = {"jdbc_type": "TIME", "java_type": "Date", "java_package": "java.util"}
    YEAR = {"jdbc_type": "DATE", "java_type": "Date", "java_package": "java.util"}
    TIMESTAMP = {"jdbc_type": "TIMESTAMP", "java_type": "Date", "java_package": "java.util"}
    BLOB = {"jdbc_type": "LONGVARBINARY", "java_type": "String", "java_package": "java.lang"}
    TINYBLOB = {"jdbc_type": "VARBINARY", "java_type": "String", "java_package": "java.lang"}
    MEDIUMBLOB = {"jdbc_type": "LONGVARBINARY", "java_type": "String", "java_package": "java.lang"}
    LONGBLOB = {"jdbc_type": "LONGVARBINARY", "java_type": "String", "java_package": "java.lang"}
    BINARY = {"jdbc_type": "BINARY", "java_type": "String", "java_package": "java.lang"}
    VARBINARY = {"jdbc_type": "VARBINARY", "java_type": "String", "java_package": "java.lang"}
    JSON = {"jdbc_type": "CHAR", "java_type": "String", "java_package": "java.lang"}


unknown_type = {"jdbc_type": "OTHER", "java_type": "Object", "java_package": "java.lang"}


def get_table_info(cursor, table_name, table_comment, database):
    cursor.execute("select t.column_name,t.data_type,t.is_nullable,t.column_key,"
                   "t.column_default,t.extra,t.column_comment from information_schema.COLUMNS t where TABLE_NAME='{}' and TABLE_SCHEMA='{}' " \
                   .format(table_name, database))
    results = cursor.fetchall()
    table = Table(*[table_name, table_comment])
    for row in results:
        table.add_field(*row)
    return table


def get_tables(cursor, database, *specific_tables):
    if specific_tables and specific_tables[0] != "*":
        in_str = ""
        flag = True
        for specific_table in specific_tables:
            if flag:
                in_str += "'" + specific_table + "'"
                flag = False
            else:
                in_str += ",'" + specific_table + "'"
        cursor.execute(
            "select TABLE_NAME,TABLE_COMMENT from information_schema.TABLES where TABLE_SCHEMA='{}' and TABLE_NAME in ({})".format(
                database, in_str))
    else:
        cursor.execute(
            "select TABLE_NAME,TABLE_COMMENT from information_schema.TABLES where TABLE_SCHEMA='{}'".format(database))
    results = cursor.fetchall()
    tables = []
    for row in results:
        tables.append(get_table_info(cursor, row[0], row[1], database))
    return tables


def mapping_java_type(meta_type):
    try:
        return JdbcType[meta_type.upper()].value
    except:
        return unknown_type


class Table:

    def __init__(self, *args):
        self.meta_data = dict(name=args[0])
        self.java_variable_name = under_line2_camel(self.meta_data['name'])
        self.java_class_name = self.java_variable_name[0].upper() + self.java_variable_name[1:]
        self.comment = args[1]
        self.fields = []
        self.import_set = set()

    def add_field(self, *arguments, **kwargs):
        f = field(*arguments, **kwargs)
        if f.java_package != "java.lang":
            self.import_set.add(f.java_package + "." + f.java_type)
        self.fields.append(f)

    def __str__(self) -> str:
        s = "meta_data : " + self.meta_data.__str__() + " | java_class_name : " \
            + self.java_class_name + " | java_variable_name : " + self.java_variable_name \
            + " | fields : [ \n"
        for f in self.fields:
            s += "{" + f.__str__() + "} \n"
        return s + "]"


class Field:

    def __init__(self, column_name, data_type, is_nullable, column_key, column_default, extra, column_comment):
        assert column_name
        assert data_type
        assert is_nullable
        assert column_key is not None
        self.meta_data = dict(
            column_name=column_name,
            data_type=data_type,
            is_nullable=is_nullable,
            column_key=column_key,
            column_default=column_default,
            extra=extra,
            column_comment=column_comment,
        )
        self.name = under_line2_camel(column_name)
        d = mapping_java_type(data_type)
        self.java_type = d['java_type']
        self.java_package = d['java_package']
        self.jdbc_type = d['jdbc_type']
        self.is_pk = column_key == "PRI"
        self.comment = column_comment
        self.is_auto_increment = self.is_pk and extra == "auto_increment"

    def full_name(self):
        return self.java_package + "." + self.java_type

    def __str__(self) -> str:
        return "meta_data : " + self.meta_data.__str__() + " | name : " \
               + self.name + " | java_type : " + self.java_type \
               + " | java_package : " + self.java_package \
               + " | jdbc_type : " + self.jdbc_type \
               + " | is_pk : " + self.is_pk.__str__() \
               + " | is_auto_increment : " + self.is_auto_increment.__str__()


def field(*arguments, **kwargs):
    return Field(*arguments, **kwargs)
