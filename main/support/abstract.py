import stat
import threading
from abc import *
from multiprocessing.pool import ThreadPool
from os.path import sep

from main.support.exception import UnsupportedOperationError
from main.utis.constants import *
from main.utis.utils import Configuration
from main.utis.utils import FileDesc


class Handler(metaclass=ABCMeta):

    @abstractmethod
    def hand(self, context):
        pass


class AbstractBaseEachTableHandler(Handler, metaclass=ABCMeta):

    def hand(self, context):
        assert isinstance(context, AbstractDbApplicationContext)
        tm = self.get_template()
        for table in context.get_tables():
            d = self.render_para(context, table)
            file_content = tm.render(d)
            context.append_file_desc(
                FileDesc(self.resolve_file_name(context, table), self.resolve_file_path(context, table), file_content))

    def render_para(self, context, table):
        return dict(table.__dict__, **context.get_config().root)

    @abstractmethod
    def get_template(self):
        pass

    @abstractmethod
    def resolve_file_name(self, context, table):
        pass

    @abstractmethod
    def resolve_file_path(self, context, table):
        pass


class Context(metaclass=ABCMeta):

    @abstractmethod
    def get_base_path(self):
        pass

    @abstractmethod
    def get_web_path(self):
        pass

    @abstractmethod
    def get_web_java_path(self):
        pass

    @abstractmethod
    def get_web_test_groovy_path(self):
        pass

    @abstractmethod
    def get_web_resources_path(self):
        pass

    @abstractmethod
    def get_web_test_resource_path(self):
        pass

    @abstractmethod
    def get_api_path(self):
        pass

    @abstractmethod
    def get_api_java_path(self):
        pass

    @abstractmethod
    def get_api_resources_path(self):
        pass

    @abstractmethod
    def get_config(self):
        pass

    @abstractmethod
    def is_success(self):
        pass

    @abstractmethod
    def error_msg(self, msg=None):
        pass

    @abstractmethod
    def append_file_desc(self, file_desc):
        pass

    @abstractmethod
    def clear_up(self):
        pass

    @abstractmethod
    def is_modularization_project(self):
        pass

    @abstractmethod
    def is_create_new(self):
        pass

    @abstractmethod
    def get_file_descs(self):
        pass


class Delivery(metaclass=ABCMeta):

    @abstractmethod
    def delivery(self, context):
        pass


class AbstractPersistentDelivery(Delivery, metaclass=ABCMeta):

    def delivery(self, context):
        file_descs = context.get_file_descs()
        remove_dir(context.get_base_path())
        try:
            self.prepare_persistent(context, file_descs)
            self.persistent(context, file_descs)
            self.post_persistent(context, file_descs)
        finally:
            context.clear_up()

    @abstractmethod
    def prepare_persistent(self, context, file_descs):
        pass

    @abstractmethod
    def persistent(self, context, file_descs):
        pass

    @abstractmethod
    def post_persistent(self, context, file_descs):
        pass


class AbstractParallelDelivery(AbstractPersistentDelivery, metaclass=ABCMeta):
    thread_pool = ThreadPool(20)

    def persistent(self, context, file_descs):
        result = []
        for file_desc in file_descs:
            result.append(self.thread_pool.apply_async(file_desc.create()))
        for r in result:
            r.wait()


class AbstractSerialDelivery(AbstractPersistentDelivery, metaclass=ABCMeta):

    def persistent(self, context, file_descs):
        for file_desc in file_descs:
            file_desc.create()


def remove_dir(dir):
    if os.path.exists(dir):
        if os.path.isfile(dir):
            os.chmod(dir, stat.S_IWRITE)
            os.remove(dir)
        else:
            for p in os.listdir(dir):
                remove_dir(os.path.join(dir, p))
            os.rmdir(dir)


class AbstractApplicationContext(Context, metaclass=ABCMeta):

    def __init__(self, config):
        assert isinstance(config, Configuration)
        self.lock = threading.Lock()
        self.path_holder = None
        self.__file_descs = []
        self.__error_msgs = []
        self.__config = config
        self.__is_create_new = config.get_necessary(IS_CREATE_NEW)
        self.app_name = config.get_necessary(APP_NAME)
        self.__is_modularization_project = config.get_necessary(IS_MODULARIZATION_PROJECT)
        self.work_path = WORK_SPACE + self.app_name
        self.make_work_path()
        self.make_dir_frame()
        self.post_init(config)

    def post_init(self, config):
        pass

    def make_dir_frame(self):
        if os.path.exists(self.work_path + self.app_name + "-web") \
                and os.path.exists(self.work_path + self.app_name + "-api"):
            self.__is_modularization_project = True
        if self.__is_modularization_project:
            self.path_holder = ModularizationProjectHolder(self.work_path, self.app_name)
        else:
            self.path_holder = SingleProjectHolder(self.work_path, self.app_name)
        self.path_holder.init_path_frame()

    def make_work_path(self):
        if os.path.exists(self.work_path):
            remove_dir(self.work_path)
        os.makedirs(self.work_path, exist_ok=True)

    def get_config(self):
        return self.__config

    def get_web_java_path(self):
        return self.path_holder.get_web_java_path()

    def get_web_resources_path(self):
        return self.path_holder.get_web_resources_path()

    def get_api_java_path(self):
        return self.path_holder.get_api_java_path()

    def get_api_resources_path(self):
        return self.path_holder.get_api_resources_path()

    def get_web_test_groovy_path(self):
        return self.path_holder.get_web_test_groovy_path()

    def get_web_test_resource_path(self):
        return self.path_holder.get_web_test_resource_path()

    def get_web_path(self):
        return self.path_holder.get_web_path()

    def get_api_path(self):
        return self.path_holder.get_api_path()

    def get_base_path(self):
        return self.work_path

    def append_file_desc(self, file_desc):
        self.lock.acquire()
        try:
            self.__file_descs.append(file_desc)
        finally:
            self.lock.release()

    def is_success(self):
        pass

    def error_msg(self, msg=None):
        if msg:
            self.__error_msgs.append(str(msg))
        return self.__error_msgs

    def is_modularization_project(self):
        return self.__is_modularization_project

    def is_create_new(self):
        return self.__is_create_new

    def clear_up(self):
        remove_dir(self.work_path)

    def get_file_descs(self):
        return self.__file_descs


class PathHolder(metaclass=ABCMeta):

    def __init__(self, work_path, app_name):
        self.work_path = work_path
        self.app_name = app_name

    @abstractmethod
    def init_path_frame(self):
        pass

    @abstractmethod
    def get_web_path(self):
        pass

    @abstractmethod
    def get_web_java_path(self):
        pass

    @abstractmethod
    def get_web_test_groovy_path(self):
        pass

    @abstractmethod
    def get_web_resources_path(self):
        pass

    @abstractmethod
    def get_api_path(self):
        pass

    @abstractmethod
    def get_api_java_path(self):
        pass

    @abstractmethod
    def get_api_resources_path(self):
        pass

    @abstractmethod
    def get_web_test_resource_path(self):
        pass


class AbstractHolder(PathHolder, metaclass=ABCMeta):

    def __init__(self, work_path, app_name):
        super().__init__(work_path, app_name)
        self.paths = self.get_init_frame_directorys()
        for k, v in self.paths.items():
            d = self.work_path + sep + v.replace("|", sep).replace("${app_name}", self.app_name)
            d = d.replace(sep + sep, sep)
            self.paths[k] = d

    def init_path_frame(self):
        for k, v in self.paths.items():
            os.makedirs(v, exist_ok=True)

    def get_web_java_path(self):
        return self.paths['web_java_path']

    def get_web_resources_path(self):
        return self.paths['web_resources_path']

    def get_api_java_path(self):
        return self.paths['api_java_path']

    def get_api_resources_path(self):
        return self.paths['api_resources_path']

    def get_web_test_groovy_path(self):
        return self.paths['web_test_groovy_path']

    def get_web_test_resource_path(self):
        return self.paths['web_test_resources_path']

    def get_web_path(self):
        return self.paths['web_path']

    def get_api_path(self):
        return self.paths['api_path']

    @abstractmethod
    def get_init_frame_directorys(self):
        pass


class ModularizationProjectHolder(AbstractHolder):
    init_frame_directorys = {
        "api_path": "${app_name}-api|",
        "api_java_path": "${app_name}-api|src|main|java|",
        "api_resources_path": "${app_name}-api|src|main|resources|",
        "web_path": "${app_name}-web|",
        "web_java_path": "${app_name}-web|src|main|java|",
        "web_resources_path": "${app_name}-web|src|main|resources|",
        "web_test_groovy_path": "${app_name}-web|src|test|groovy|",
        "web_test_resources_path": "${app_name}-web|src|test|resources|",
    }

    def get_init_frame_directorys(self):
        return self.init_frame_directorys.copy()


class SingleProjectHolder(AbstractHolder):
    init_frame_directorys = {
        "web_path": "",
        "web_java_path": "|src|main|java|",
        "web_resources_path": "|src|main|resources|",
        "web_test_groovy_path": "|src|test|groovy|",
        "web_test_resources_path": "|src|test|resources|",
    }

    def get_init_frame_directorys(self):
        return self.init_frame_directorys.copy()

    def get_api_java_path(self):
        raise UnsupportedOperationError()

    def get_api_resources_path(self):
        raise UnsupportedOperationError()

    def get_api_path(self):
        raise UnsupportedOperationError()


class AbstractDbApplicationContext(AbstractApplicationContext, metaclass=ABCMeta):

    @abstractmethod
    def create_db_connect(self):
        pass

    @abstractmethod
    def get_tables(self):
        pass
