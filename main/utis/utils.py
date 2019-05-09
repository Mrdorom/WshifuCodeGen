import json
import os

from main.support.exception import ConfigurationError

sep = os.sep


def under_line2_camel(source, sy='_'):
    if not source:
        return source
    source = str(source)
    result = ""
    length = len(source)
    i = 0
    while i < length:
        s = source[i]
        if s == sy:
            result += source[i + 1].upper()
            i += 1
        else:
            result += s
        i += 1
    return result


def camel2_under_line(source):
    if not source:
        return source
    source = str(source)
    result = ""
    for s in source:
        if s.isupper():
            result += ("_" + s.lower())
        else:
            result += s
    return result


class Configuration:
    def __init__(self, root):
        assert root is not None and isinstance(root, dict)
        self.root = root

    def get_configuration(self, key):
        var = self.get(key)
        return Configuration.from_dic(var)

    def get_list(self, key):
        result = self.get(key)
        assert isinstance(result, list)
        return result

    def get_list_configuration(self, key):
        li = self.get_list(key)
        result = []
        for r in li:
            result.append(Configuration.from_dic(r))
        return result

    def get(self, key):
        if key == '' or key is None:
            return self.root
        target = self.root
        for path in self.__key_split(key):
            target = self.__find_as_list(path, target) \
                if self.__is_list_path(path) else self.__find_as_dict(path, target)
        return target

    def get_necessary(self, key):
        target = self.get(key)
        if not target:
            raise ConfigurationError()
        return target

    @classmethod
    def from_json_str(cls, json_srt):
        assert type(json_srt) == str
        data = json.loads(json_srt)
        return cls.from_dic(data)

    @classmethod
    def from_dic(cls, dic):
        assert type(dic) == dict
        c = Configuration(dic)
        return c

    def __is_list_path(self, path):
        return path.find("[") >= 0 and path.find("]") >= 0

    def __find_as_dict(self, path, target):
        assert isinstance(target, dict)
        return target[path] if path in target else None

    def __find_as_list(self, path, target):
        assert isinstance(target, list)
        path = path.replace("[", "").replace("]", "")
        index = int(path)
        if index <= 0 or index > len(target) - 1:
            raise ConfigurationError("index out of bound for {} with {}", target, index)
        return target[index]

    def __key_split(self, key):
        return key.replace("[", ".[").split(".")


class FileDesc:

    def __init__(self, file_name, file_path, file_content):
        self.file_name = file_name
        self.file_path = file_path
        self.file_content = file_content

    def create(self):
        path = self.file_path
        while path.__contains__(sep + sep):
            path = path.replace(sep + sep, sep)
        os.makedirs(path, **{"exist_ok": True})
        while path.__contains__(sep + sep):
            path = path.replace(sep + sep, sep)
        file_path = path + sep + self.file_name
        file = open(file_path, **dict(mode="w+", encoding="utf-8"))
        file.write(self.file_content)


def package_to_path(package, base_path):
    path = package.replace(".", sep)
    if base_path:
        if base_path.endswith(sep):
            path = base_path + path
        else:
            path = base_path + sep + path
    return path


def none_replace_format(string, *args):
    l = []
    for a in args:
        l.append(a if a else "")
    return string.format(*l)


def main():
    c = Configuration.from_json_str(
        """{"a":113, "b":443, "c":{"c1":"c1","c2":456}, "d":[123,412,512], "e":{"e1":[{"e1_0": "e.e1[0].e1_0"},{"e1_0": "e.e1[1].e1_0"}]}, "f":{"f1":["asz","qwezx"]}}""")
    print(c.get("a"))
    print(c.get("b"))
    print(c.get("c.c1"))
    print(c.get("c.c2"))
    print(c.get("d[0]"))
    print(c.get("e.e1[0].e1_0"))
    print(c.get_list("f.f1"))
    print(under_line2_camel("asdq_zxcq_qa_asd"))
    print(camel2_under_line("asdqZxcqQaAsd"))


if __name__ == "__main__":
    main()
