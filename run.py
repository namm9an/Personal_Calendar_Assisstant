import sys
import os
import uvicorn

# Get the absolute path of the directory containing this script
project_root = os.path.abspath(os.path.dirname(__file__))

# Add the project root to the Python path
sys.path.insert(0, project_root)

# Create a simple file to define module paths if needed
with open(os.path.join(project_root, "app", "__init__.py"), "a"):
    pass

if __name__ == "__main__":
    # Change the working directory to the project root
    os.chdir(project_root)
    
    # Run the app module
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True) 