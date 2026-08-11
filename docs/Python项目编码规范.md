# Python 编码规范

[TOC]

## 一、📄 文档说明

本规范基于 PEP 8、PEP 20（Python 之禅）及行业通用实践制定，适用于团队所有 Python 项目的**语言层编码风格**（缩进/空格/导入/注释/类型注解/控制流/函数类/命名/测试/提交），与具体框架无关，旨在保障代码可读性、可维护性与协作一致性。

<br/>

## 二、✏️ 代码格式规范

### 2.1 缩进与换行

- 缩进：统一使用 **4 个空格**，禁止使用 Tab（编辑器需配置"Tab 自动转为 4 空格"）；
- 行长度：单行代码不超过 120 个字符（项目 Ruff 配置），注释/文档字符串不超过 80 个字符；
- 换行原则：
    - 二元运算符后换行（如 +、=、and/or）；
    - 函数/类参数列表过长时，换行后缩进 4 空格，末尾括号单独换行；

    ```python
    # 正确
    def get_user_list(
        user_type: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        pass

    # 错误
    def get_user_list(user_type: str, page: int = 1, page_size: int = 20) -> List[Dict[str, Any]]:  # 行过长
    ```

- 空行：
    - 模块级：函数/类之间空 2 行，类内方法之间空 1 行；
    - 逻辑块：代码逻辑独立块之间空 1 行，避免无意义空行。

### 2.2 空格使用

- 二元运算符（=、+、-、\*、/、== 等）两侧各加 1 个空格；
- 函数/方法参数列表中，逗号后加 1 个空格，等号（默认参数）两侧加空格；
- 括号内侧无空格（如 `list(user_ids)` 而非 `list( user_ids )`）；
- 切片语法空格：`arr[1:5]`（正确），`arr[1 : 5]`（错误）。

```python
# ✅ 正确 — 运算符两侧有空格
total = num1 + num2 * (num3 - num4)


def func(a: int, b: str = "default") -> None:
    pass


# ❌ 错误 — 运算符两侧缺少空格
total = num1+num2*(num3-num4)


def func(a:int, b:str="default") -> None:
    pass
```

<br/>

## 三、🧱 语法与代码风格

### 3.1 导入规范

- 导入顺序：标准库 → 第三方库 → 项目内部库，各组之间空 1 行；
- 导入方式：
    - 禁止通配符导入（`from module import *`），避免命名冲突；
    - 优先使用**绝对导入**，禁止相对导入，避免隐式依赖与 IDE 跳转困难；
    - 单行只导入一个模块/对象，禁止一行多导入（除分组导入）；

```python
# 正确（绝对导入）
import os
import sys

import requests
import pandas as pd

from project.core import auth
from project.utils import time_utils

# 错误（相对导入）
from ..core import auth
from ...utils import time_utils
```

- 别名规范：通用别名统一（如 `import numpy as np`、`import pandas as pd`），自定义别名需语义化，禁止无意义别名（如 `import user as u`）；
- 未使用的导入：仅导入实际使用的类型，避免导入但未使用的警告；

```python
# ❌ 错误
from typing import Any, Optional, Sequence, TypeVar

# ✅ 正确
from typing import Any, TypeVar
```

### 3.2 注释规范

- 单行注释：`#` 后加 1 个空格，注释内容与代码空 2 个空格（如 `x = 10  # 存储用户ID`）；
- 块注释：多行注释用 `#` 开头，对齐缩进，说明复杂逻辑；
- 文档字符串（Docstring）：
    - 复杂函数/公开 API 必须写 docstring，格式统一使用 Google 风格；
    - 简单函数（如 getter/setter、工具函数）可省略 docstring，代码自解释即可；
    - 包含功能说明、参数、返回值、异常（如有）、示例（复杂函数）；

```python
# 复杂函数 - 需要 docstring
def calculate_sum(num1: int, num2: int) -> int:
    """计算两个整数的和。

    Args:
        num1: 第一个整数
        num2: 第二个整数

    Returns:
        两个数的和

    Examples:
        >>> calculate_sum(1, 2)
        3
    """
    return num1 + num2


# 简单函数 - 可省略 docstring
def get_user_name(user_id: int) -> str:
    return user_cache.get(user_id, {}).get("name", "")
```

- 注释原则：注释"为什么"而非"是什么"，代码本身应自解释，避免冗余注释。

### 3.3 数据类型与类型注解

#### 3.3.1 函数类型注解

- 强制使用类型注解：函数/方法的参数、返回值必须添加类型注解，复杂类型用 `typing` 模块（Python 3.9+ 可直接用内置类型）；

```python
# 正确（Python 3.9+）
def process_user(user_id: int, user_info: dict[str, str]) -> list[int]:
    pass


# 正确（Python 3.8及以下）
from typing import Dict, List


def process_user(user_id: int, user_info: Dict[str, str]) -> List[int]:
    pass
```

- 类型变量：当函数需要处理多种类型时，使用 `TypeVar`；

```python
from typing import TypeVar

T = TypeVar("T")


def pick(arr: list[T]) -> T:
    return random.choice(arr)
```

#### 3.3.2 类属性与实例属性

- 类属性类型注解：类级别属性必须声明类型；

```python
# ❌ 错误
class Config:
    DEFAULTS = {...}
    SUPPORTED_MODES = ["read", "write", ...]


# ✅ 正确
class Config:
    DEFAULTS: dict[str, str] = {...}
    SUPPORTED_MODES: list[str] = ["read", "write", ...]
```

- 实例属性类型注解：在类体中显式声明实例属性类型；

```python
# ❌ 错误
class Worker:
    def __init__(self, path: str) -> None:
        self.path = path
        self.conn = connect(path)


# ✅ 正确
class Worker:
    path: str
    conn: Connection

    def __init__(self, path: str) -> None:
        self.path = path
        self.conn = connect(path)
```

#### 3.3.3 局部变量与容器

- 局部变量类型注解：列表/字典等容器变量显式标注类型；

```python
# ❌ 错误
rows = []
for item in data:
    rows.append({...})

# ✅ 正确
from typing import Any

rows: list[dict[str, Any]] = []
for item in data:
    rows.append({...})
```

- 容器初始化：优先使用字面量（`[]`/`{}`/`()`）而非 `list()`/`dict()`/`tuple()`；
- 空值判断：判断列表/字典是否为空用 `if not data` 而非 `if len(data) == 0`；

#### 3.3.4 None 与可选类型

- 可选类型处理：对于可能为 `None` 的值，使用 `Optional` 或 `| None`（Python 3.10+），并在使用前进行非空判断；

```python
# 正确
from typing import Optional


def get_value(key: str) -> Optional[str]:
    return cache.get(key)


value = get_value("name")
if value is not None:
    print(value.upper())


# Python 3.10+
def get_value(key: str) -> str | None:
    return cache.get(key)
```

- None 与联合类型：明确区分 `None` 和空值的语义，根据场景选择：
    - 数据库字段：`NULL` 用 `None`，空值用 `""` 或 `0`
    - API 响应：缺失字段用 `None`，空值保持原类型
    - 函数返回值：无结果用 `None`，空结果用空容器（`[]`/`{}`）

```python
# 场景1：数据库字段 — 根据业务语义选择
row["expires_at"] = some_date.isoformat() if condition else None  # NULL 表示未设置
row["description"] = description if description else ""           # 空字符串表示无描述

# 场景2：函数返回值 — 无结果用 None，空结果用空容器
def find_user(user_id: int) -> dict | None:
    """未找到返回 None"""
    return user_cache.get(user_id)

def get_tags(item_id: int) -> list[str]:
    """无标签返回空列表"""
    return item_tags.get(item_id, [])
```

#### 3.3.5 无类型第三方库

- 无类型第三方库：部分第三方库无类型存根，可用 `# type: ignore` 抑制导入警告，或安装 `types-<package>` 类型存根；

```python
# 方案一：抑制导入警告
import bcrypt  # type: ignore


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
```

> **推荐方案**: 优先安装 `pip install types-<package>`（如 `types-bcrypt`），或为项目编写 `.pyi` 类型存根文件。

#### 3.3.6 动态数据源

- 动态数据源：从 ORM 查询结果、`dict` 取值等动态数据源取值时，显式转换为目标类型（`str()`/`int()`），或用 `typing.cast` 处理复杂类型，避免 `Any` 扩散；

```python
# ❌ 错误 — data[key] 类型为 Any
result = LOOKUP_TABLE[hash(data["key"]) % len(LOOKUP_TABLE)]

# ✅ 正确 — 显式转换为 str
result = LOOKUP_TABLE[hash(str(data["key"])) % len(LOOKUP_TABLE)]
```

- 外部数据源结果：数据库查询、API 响应等无类型注解的外部数据源，其返回值被推断为 `Any`；

```python
# ✅ 正确 — 数据库查询
count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # type: ignore

# ✅ 正确 — JSON 反序列化
data = json.loads(raw)  # type: ignore
```

> 如果先为变量添加了类型注解（如 `rows: list[dict[str, Any]]`），后续对该变量的迭代/使用不需要额外忽略。

### 3.4 控制流与异常处理

- 条件语句：
    - 单行条件仅用于简单场景（如 `x = 1 if flag else 0`），复杂逻辑拆多行；
    - 多条件判断优先用 `if/elif/else`，避免多层嵌套（超过 3 层需拆分函数）；
- 循环语句：
    - 优先使用列表推导/生成器表达式替代简单循环（如 `[x*2 for x in lst if x > 0]`）；
    - 避免无退出条件的无限循环（`while True`），常驻服务场景（如调度器、服务器）可使用 `while True`，需添加 `KeyboardInterrupt` 捕获以支持优雅退出；
- 异常处理：
    - 精准捕获异常（如 `except ValueError` 而非 `except Exception`）；
    - `try/except` 仅包裹必要代码，避免"大 try 块"；
    - 捕获异常后必须处理（日志/提示），禁止空 `except`；
    ```python
    # 正确
    try:
        num = int(input("输入数字："))
    except ValueError as e:
        logger.error(f"输入非数字：{e}")
        raise ValueError("请输入有效的整数") from e  # 保留异常栈
    ```

### 3.5 函数与类规范

- 函数：
    - 单一职责：一个函数仅做一件事，建议不超过 50 行，过长应考虑拆分；
    - 默认参数：禁止使用可变对象（列表/字典）作为默认参数（改用 `None`）；

    ```python
    # 正确
    def add_item(item, lst=None):
        if lst is None:
            lst = []
        lst.append(item)
        return lst


    # 错误
    def add_item(item, lst=[]):  # 可变默认参数会复用
        lst.append(item)
        return lst
    ```

- 类：
    - 类名遵循大驼峰，必须有 docstring 说明类用途；
    - 继承：优先使用组合而非继承，继承层级不超过 3 层；
    - 魔术方法：仅实现必要的魔术方法（如 `__init__`/`__str__`），禁止滥用；
    - 私有成员：仅用单下划线（`_private`）标识，双下划线（`__`）仅用于避免子类覆盖。

<br/>

## 四、🏷️ 命名规范

### 4.1 核心原则

1. 遵循 PEP 8 官方规范，兼顾可读性与代码兼容性；
2. 全小写为主，禁止混用分隔符，命名语义化（见名知意）。

### 4.2 具体命名规则

| 命名对象 | 格式要求 | 正确示例 | 错误示例 |
| -------- | -------- | -------- | -------- |
| 项目名/仓库名/PyPI 包名 | 连字符分隔（kebab-case） | user-management-system | user_management_system |
| 文件名/模块名/包名 | 下划线分隔（snake_case） | user_info.py、auth_core/ | user-info.py、authCore/ |
| 变量/函数/方法名 | 下划线分隔（snake_case） | user_name、get_user_info() | userName、getUserInfo() |
| 类名/异常类名 | 大驼峰（CamelCase） | UserInfo、AuthError | user_info、auth_error |
| 常量名 | 全大写+下划线 | MAX_RETRY、TIMEOUT_SEC | MaxRetry、timeout_sec |
| 私有成员（变量/方法） | 单下划线开头+snake_case | _private_var、_check_auth() | __privateVar、-checkAuth() |

### 4.3 补充规范

1. 命名长度：简洁不冗余，避免过长（如用 user_info 而非 user_information_of_system）；
2. 禁用字符：禁止使用中文、特殊符号（\_/- 除外）、空格，禁止以数字开头；
3. 跨场景适配：项目名（连字符）与内部包名（下划线）需对应（如仓库名 user-auth → 包名 user_auth）。

### 4.4 检查与落地

1. 强制使用工具：通过 `ruff` 检查命名与格式规范，纳入代码提交流程；
2. 例外处理：特殊场景需偏离规范时，需团队评审并在代码注释中说明原因。

<br/>

## 五、🔍 类型检查规范

### 5.1 类型抑制规则

- `# type: ignore` 抑制该行所有类型错误（通用写法）；
- 特定类型检查器（如 mypy、pyright）支持 `# type: ignore[ruleCode]` 仅抑制指定规则；
- 多规则同时抑制时，用逗号分隔：`# type: ignore[rule1, rule2]`；

### 5.2 未使用返回值

- 函数调用返回的非 `None` 值未被使用时，用 `_ =` 显式丢弃；

```python
# ❌ 错误
conn.execute("DROP TABLE IF EXISTS users")

# ✅ 正确
_ = conn.execute("DROP TABLE IF EXISTS users")
```

### 5.3 检查工具

| 工具 | 用途 |
|------|------|
| `mypy` | 静态类型检查 |
| `pyright` | 静态类型检查，VSCode/IDE 集成 |

> 工具特定规则（如 pyright ignore）请参考工具官方文档。

<br/>

## 六、🧪 测试规范

- 测试框架：统一使用 `pytest`，覆盖率统计用 `pytest-cov`；
- 测试覆盖率：核心业务代码覆盖率建议 80% 以上，根据项目性质酌情调整；
- 测试命名：测试文件以 `test_` 开头，测试函数/类以 `test_` 开头；

```python
# test_user.py
def test_get_user_info():
    assert get_user_info(1) == {"name": "test"}
```

- 测试原则：测试用例独立，不依赖外部环境（使用 mock 替代真实数据库/接口）；
- 测试目录：置于项目 `tests/` 目录，区分 `unit/`（单元测试）与 `integration/`（集成测试）。

<br/>

## 七、📦 版本与提交规范

- 版本号：遵循语义化版本（MAJOR.MINOR.PATCH），如 1.2.3；
    - MAJOR：不兼容的 API 变更；
    - MINOR：新增功能，兼容旧版本；
    - PATCH：修复 bug，兼容旧版本；
- 提交规范：提交信息遵循 `类型: 描述` 格式，如 `feat: 新增用户登录接口`、`fix: 修复用户信息查询bug`；
  类型包括：feat（功能）、fix（修复）、docs（文档）、style（格式）、refactor（重构）、test（测试）、chore（构建）。

<br/>

## 八、📋 例外处理

- 特殊场景需偏离本规范时，需经团队核心成员评审通过；
- 偏离部分需在代码/文档中注明原因，且仅局限于特定场景，不扩散。
