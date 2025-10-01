"""Test helper libraries following modern testing standards."""

# Import main helper classes for easy access
from .assertions import (
    AssertionContext,
    assert_auth_response_structure,
    assert_authentication_error,
    assert_authorization_error,
    assert_error_response_structure,
    assert_field_types,
    assert_health_response,
    assert_json_response,
    assert_list_response,
    assert_not_found_error,
    assert_pagination_response,
    assert_required_fields,
    assert_response_structure,
    assert_response_time,
    assert_status_code,
    assert_success_response,
    assert_user_response_structure,
    assert_validation_error,
    assert_vocabulary_response_structure,
)
from .auth_helpers import (
    AsyncAuthHelper,
    AuthHelper,
    AuthTestHelperAsync,  # For backward compatibility
    AuthTestScenarios,
    create_auth_fixtures,
)
from .data_builders import (
    CEFRLevel,
    TestDataSets,
    TestUser,
    TestVocabularyWord,
    UserBuilder,
    VocabularyWordBuilder,
    create_user,
    create_vocabulary_word,
)

__all__ = [
    "AssertionContext",
    "AsyncAuthHelper",
    # Authentication helpers
    "AuthHelper",
    "AuthTestHelperAsync",
    "AuthTestScenarios",
    "CEFRLevel",
    "TestDataSets",
    "TestUser",
    "TestVocabularyWord",
    # Data builders
    "UserBuilder",
    "VocabularyWordBuilder",
    "assert_auth_response_structure",
    "assert_authentication_error",
    "assert_authorization_error",
    "assert_error_response_structure",
    "assert_field_types",
    "assert_health_response",
    "assert_json_response",
    "assert_list_response",
    "assert_not_found_error",
    "assert_pagination_response",
    "assert_required_fields",
    "assert_response_structure",
    "assert_response_time",
    # Assertion helpers
    "assert_status_code",
    "assert_success_response",
    "assert_user_response_structure",
    "assert_validation_error",
    "assert_vocabulary_response_structure",
    "create_auth_fixtures",
    "create_user",
    "create_vocabulary_word",
]
