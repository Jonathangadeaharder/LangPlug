#!/usr/bin/env python3
"""
Test ProcessingStatus model validation directly
"""

from api.models.processing import ProcessingStatus

print("Testing ProcessingStatus model validation...")

# Test creating a ProcessingStatus with 'starting' status
try:
    status = ProcessingStatus(
        status="starting",
        progress=0.0,
        current_step="Initializing",
        message="Test message"
    )
    print(f"✅ SUCCESS: Created ProcessingStatus with status='starting'")
    print(f"   Status: {status.status}")
    print(f"   Progress: {status.progress}")
    print(f"   Step: {status.current_step}")
except Exception as e:
    print(f"❌ ERROR: Failed to create ProcessingStatus with status='starting'")
    print(f"   Error: {e}")

# Test the model schema
print("\nModel schema:")
print(ProcessingStatus.model_json_schema())

# Test all valid statuses
valid_statuses = ["starting", "processing", "completed", "error"]
for status_val in valid_statuses:
    try:
        test_status = ProcessingStatus(
            status=status_val,
            progress=50.0,
            current_step="Test step",
            message="Test message"
        )
        print(f"✅ Status '{status_val}' is valid")
    except Exception as e:
        print(f"❌ Status '{status_val}' failed: {e}")