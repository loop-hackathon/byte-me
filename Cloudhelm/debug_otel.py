try:
    import opentelemetry.instrumentation.sqlalchemy
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
