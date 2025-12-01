# Test importing dependencies directly without going through core.__init__
try:
    pass
except Exception as e:
    import traceback

    traceback.print_exc()
