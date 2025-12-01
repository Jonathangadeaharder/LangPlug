2025-11-30 17:55:16 [warning  ] slowapi not installed - rate limiting disabled. Install with: pip install slowapi==0.1.9
Starting reproduction script...
2025-11-30 17:55:16 [info     ] TokenBlacklist initialized (in-memory)
2025-11-30 17:55:16 [info     ] Authentication services initialized (TokenBlacklist, LoginTracker - in-memory)
2025-11-30 17:55:17 [warning  ] LANGPLUG_ADMIN_PASSWORD environment variable not set. Please set a strong password for the admin account. Using a temporary secure password for this session.
2025-11-30 17:55:17 [info     ] Temporary admin password generated - check logs securely
2025-11-30 17:55:17 [info     ] Default admin user created (username: admin, email: admin@langplug.com). Password from LANGPLUG_ADMIN_PASSWORD environment variable.
DEBUG: seed_test_data called. TEST_DATA present: True
DEBUG: Found 3 users in TEST_DATA
DEBUG: Users list: ['testuser', 'student1', 'teacher1']
DEBUG: Processing testuser
DEBUG: Checking existence of testuser
DEBUG: Creating user testuser
DEBUG: Calling hash_password...
DEBUG: hash_password done.
DEBUG: Instantiating User...
DEBUG: User instantiated.
DEBUG: Adding user to session...
DEBUG: User added to session.
DEBUG: Added user testuser to session. Flushing...
DEBUG: Flushed user testuser
DEBUG: Processing student1
DEBUG: Checking existence of student1
DEBUG: Creating user student1
DEBUG: Calling hash_password...
DEBUG: hash_password done.
DEBUG: Instantiating User...
DEBUG: User instantiated.
DEBUG: Adding user to session...
DEBUG: User added to session.
DEBUG: Added user student1 to session. Flushing...
DEBUG: Flushed user student1
DEBUG: Processing teacher1
DEBUG: Checking existence of teacher1
DEBUG: Creating user teacher1
DEBUG: Calling hash_password...
DEBUG: hash_password done.
DEBUG: Instantiating User...
DEBUG: User instantiated.
DEBUG: Adding user to session...
DEBUG: User added to session.
DEBUG: Added user teacher1 to session. Flushing...
DEBUG: Flushed user teacher1
DEBUG: Committing session...
2025-11-30 17:55:17 [info     ] Seeded 3 users from TEST_DATA
DEBUG: Seeding complete
SUCCESS: init_db completed without error.
