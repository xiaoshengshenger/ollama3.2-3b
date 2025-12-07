import os
import re
import typing
from typing import Any, TextIO

from yaml import SafeLoader

_env_replace_matcher = re.compile(r"\$\{(\w|_)+:?.*}")


@typing.no_type_check
def load_yaml_with_envvars(
    stream: TextIO, environ: dict[str, Any] = os.environ
) -> dict[str, Any]:
    """加载YAML文件并替换环境变量"""
    loader = SafeLoader(stream)

    def load_env_var(_, node) -> str:
        value = str(node.value).removeprefix("${").removesuffix("}")
        split = value.split(":", 1)
        env_var = split[0]
        value = environ.get(env_var)
        default = None if len(split) == 1 else split[1]
        if value is None and default is None:
            raise ValueError(
                f"环境变量 {env_var} 未设置且未提供默认值"
            )
        return value or default

    loader.add_implicit_resolver("env_var_replacer", _env_replace_matcher, None)
    loader.add_constructor("env_var_replacer", load_env_var)

    try:
        return loader.get_single_data()
    finally:
        loader.dispose()