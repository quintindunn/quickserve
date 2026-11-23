@echo off

echo "Creating virtual environment..."
py -m venv .venv
call .venv/Scripts/activate
echo "Done!"

echo "Installing requirements..."
py -m pip install -e .
echo "Done!"

echo "Create an admin account!"
py src/manager.py createadmin
echo "Done!"

echo "Start the server by executing `run-windows.bat`!"
