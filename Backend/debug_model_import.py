#!/usr/bin/env python3
"""
Debug ProcessingStatus model import and validation
"""

import sys
print("Python path:")
for path in sys.path:
    print(f"  {path}")

print("\n" + "="*50)
print("Importing ProcessingStatus...")

try:
    from api.models.processing import ProcessingStatus
    print(f"✅ Successfully imported ProcessingStatus from: {ProcessingStatus.__module__}")
    print(f"   File location: {ProcessingStatus.__module__.__file__ if hasattr(ProcessingStatus.__module__, '__file__') else 'Unknown'}")
    
    # Check the model definition
    schema = ProcessingStatus.model_json_schema()
    status_field = schema.get('properties', {}).get('status', {})
    print(f"\nStatus field definition:")
    print(f"   Type: {status_field.get('type')}")
    print(f"   Enum values: {status_field.get('enum')}")
    
    # Test creating with 'starting' status
    try:
        test_status = ProcessingStatus(
            status="starting",
            progress=0.0,
            current_step="Test",
            message="Test message"
        )
        print(f"\n✅ SUCCESS: Created ProcessingStatus with 'starting' status")
    except Exception as e:
        print(f"\n❌ FAILED: Cannot create ProcessingStatus with 'starting' status")
        print(f"   Error: {e}")
        
except ImportError as e:
    print(f"❌ Failed to import ProcessingStatus: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")

print("\n" + "="*50)
print("Checking for other ProcessingStatus definitions...")

# Check if there are multiple ProcessingStatus classes in memory
import gc
for obj in gc.get_objects():
    if hasattr(obj, '__name__') and obj.__name__ == 'ProcessingStatus' and hasattr(obj, '__module__'):
        print(f"Found ProcessingStatus class in module: {obj.__module__}")