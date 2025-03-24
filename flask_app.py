import os
import sys

# Add your project directory to Python path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

path = '/home/va1ts/projekts2'
if path not in sys.path:
    sys.path.append(path)

os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_SECRET_KEY'] = 'your-secret-key'

from app import app as application

# Start the automation thread when WSGI loads
if not hasattr(application, '_automation_started'):
    from app import fan_assignments, fan_lock, automation_worker
    import threading
    
    automation_thread = threading.Thread(
        target=automation_worker,
        args=(fan_assignments, fan_lock),
        daemon=True
    )
    automation_thread.start()
    application._automation_started = True