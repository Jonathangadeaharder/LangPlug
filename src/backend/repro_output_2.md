C:\Users\Jonandrop\AppData\Roaming\Python\Python313\site-packages\passlib\pwd.py:16: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
2025-11-30 17:51:20 [warning  ] slowapi not installed - rate limiting disabled. Install with: pip install slowapi==0.1.9
Starting reproduction script...
2025-11-30 17:51:20 [warning  ] LANGPLUG_ADMIN_PASSWORD environment variable not set. Please set a strong password for the admin account. Using a temporary secure password for this session.
2025-11-30 17:51:20 [info     ] Temporary admin password generated - check logs securely
Traceback (most recent call last):
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\reproduce_issue.py", line 29, in main
    await init_db()
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\database\database.py", line 83, in init_db
    await create_default_admin_user()
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\database\database.py", line 178, in create_default_admin_user
    hashed_password = SecurityConfig.hash_password(admin_password)
  File "C:\Users\Jonandrop\IdeaProjects\LangPlug\src\backend\core\auth\auth_security.py", line 123, in hash_password
    from pwdlib import PasswordHash
ModuleNotFoundError: No module named 'pwdlib'
FAILURE: init_db failed with error: No module named 'pwdlib'
