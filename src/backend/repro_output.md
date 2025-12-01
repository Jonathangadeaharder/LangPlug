C:\Users\Jonandrop\AppData\Roaming\Python\Python313\site-packages\passlib\pwd.py:16: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
Traceback (most recent call last):
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\reproduce_issue.py", line 21, in <module>
    from core.database.database import init_db
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\__init__.py", line 4, in <module>
    from .auth import *  # noqa
    ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\auth\__init__.py", line 2, in <module>
    from .auth import *
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\auth\auth.py", line 18, in <module>
    from core.config import settings
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\config\__init__.py", line 2, in <module>
    from .config import *
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\config\config.py", line 212, in <module>
    settings = Settings()
  File "C:\Users\Jonandrop\AppData\Roaming\Python\Python313\site-packages\pydantic_settings\main.py", line 188, in __init__
    super().__init__(
    ~~~~~~~~~~~~~~~~^
        **__pydantic_self__._settings_build_values(
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<27 lines>...
        )
        ^
    )
    ^
  File "C:\Users\Jonandrop\AppData\Roaming\Python\Python313\site-packages\pydantic\main.py", line 253, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
LANGPLUG_SECRET_KEY
  String should have at least 32 characters [type=string_too_short, input_value='test_secret_key_repro', input_type=str]
    For further information visit https://errors.pydantic.dev/2.11/v/string_too_short
