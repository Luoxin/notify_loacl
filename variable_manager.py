import json
import os
import traceback
import yaml
from enum import Enum, unique


class VariableManagerException(Exception):
    """variable manager base exception"""


class LoadFileNotFound(FileNotFoundError, VariableManagerException):
    """load file is not exist"""


class InvalidConfigurationFile(VariableManagerException, yaml.scanner.ScannerError):
    """Invalid configuration file"""


class UnsupportedConfigurationFileTypes(VariableManagerException):
    """Unsupported configuration file types"""


class VariableManager(object):
    _supported_file_types = ["yaml"]

    def __init__(self, load_file=False, file_type: str = "yaml"):
        self.load_file_path = ""
        self._variable = None
        self.file_type = ""
        if load_file:
            self.reload_file(load_file=load_file, file_type=file_type)

    def set_val(self, key: str, value):
        self._variable[key] = value

    def set_load_file(self, load_file=False, file_type: str = "yaml") -> bool:
        """
        :param file_type: 如果加载文件有效，此变量才生效，默认yaml，其他类型正在添加支持
        :param load_file: 如果不传入，默认不加载文件，如果传入
                            如果传入True，使用默认路径加载文件
                            如果传入指定路径，使用指定路径加载文件
        :return bool: 返回是否修改成功
        """
        if isinstance(load_file, bool):
            if load_file:
                try:
                    from .utils import get_val_file_path

                    self.load_file_path = get_val_file_path()
                except:
                    pass
            else:
                return False
        elif isinstance(load_file, str):
            self.load_file_path = load_file
        elif isinstance(load_file, dict):
            self._variable = load_file
            self.file_type = "json"
            return False

        self.set_load_file_type(file_type=file_type)
        return True

    def set_load_file_type(self, file_type: str = "yaml"):
        """
        :param file_type: 如果加载文件有效，此变量才生效，默认yaml，其他类型正在添加支持
        :return:
        """
        if file_type not in self._supported_file_types:
            raise UnsupportedConfigurationFileTypes()
        self.file_type = file_type

    def reload_file(self, load_file=False, file_type: str = "yaml"):
        if not self.set_load_file(load_file=load_file, file_type=file_type):
            return

        if self.load_file_path is None:
            print("配置文件为找到")

        # 先判断配置文件是否存在，后期做默认配置
        if not os.path.exists(self.load_file_path):
            raise FileNotFoundError()

        if self.file_type == "yaml":
            try:
                with open(self.load_file_path, encoding="utf-8") as f:
                    self._variable = yaml.load(f, Loader=yaml.FullLoader)
            except yaml.scanner.ScannerError:
                traceback.print_exc()
                raise InvalidConfigurationFile()
        else:
            raise UnsupportedConfigurationFileTypes()

    def get_val(self, key):
        try:
            return self._variable.get(key)
        except:
            return None

    def get_val_str(self, key, default: str = ""):
        try:
            value = self.get_val(key)
            return str(value) if value is not None else default
        except:
            return default

    def get_val_int(self, key, default: int = 0):
        try:
            value = self.get_val(key)
            return int(value) if value is not None else default
        except:
            return default

    def get_val_float(self, key, default: float = 0.0):
        try:
            value = self.get_val(key)
            return float(value) if value is not None else default
        except:
            return default

    def get_val_bool(self, key, default: bool = False):
        try:
            value = self.get_val(key)
            return bool(value) if value is not None else default
        except:
            return default

    def get_val_dict(self, key, default: dict = None):
        if default is None:
            default = {}
        try:
            value = self.get_val(key)
            return dict(value) if value is not None else default
        except:
            return default

    def get_val_json(self, key, default: dict = None):
        if default is None:
            default = {}
        try:
            value = self.get_val(key)
            return json.loads(value) if value is not None else default
        except:
            return default

    def get_val_list(self, key, default: list = None):
        if default is None:
            default = []
        try:
            value = self.get_val(key)
            return list(value) if value is not None else default
        except:
            return default

    def get_val_list_int(self, key, default: list = None):
        if default is None:
            default = []
        try:
            value = self.get_val(key)

            temp = []
            if isinstance(value, list):
                for item in value:
                    try:
                        temp.append(int(item))
                    except:
                        pass
            else:
                temp = default

            return temp
        except:
            return default

    def get_val_all(self):
        return self._variable

    def get_val_enum(self, key, default: Enum = None):
        try:
            value = self.get_val(key)
            if isinstance(value, Enum):
                return value
            return default
        except:
            return default

    def get_val_with_type(self, key, value_type, default: Enum = None):
        try:
            value = self.get_val(key)
            if isinstance(value, value_type):
                return value
            return default
        except:
            return default

    def is_has(self, key) -> bool:
        if isinstance(self._variable, dict) and key in self._variable.keys():
            return True

        return False

    def get_val_uint(self, key, default: 0):
        val = self.get_val_int(key, default)
        if val < 0:
            val = 0
        return val

    def add_val(self, key, val):
        self._variable[key] = val
