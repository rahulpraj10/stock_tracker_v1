import os
try:
    os.makedirs("test_dir")
    print("Created test_dir")
except Exception as e:
    print(f"Error: {e}")
