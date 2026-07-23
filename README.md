Task Manager

A modern Django task management system with role-based access, project management, analytics, and PWA support.

Features
- Authentication
- Role-based access (Manager & Employee)
- Task management
- Project management
- Dashboard analytics
- Profile management
- Responsive UI
- PWA support
- REST API
- Background tasks with Celery

Technologies
- Django
- Tailwind CSS
- DaisyUI
- Vite
- SQLite (Development)
- PostgreSQL (Production)
- Redis
- Celery
- Docker

Quick Start

 Clone
git clone ... 

 Install
make init

 Run
Terminal 1
make start

Terminal 2
make npm-dev

Visit:
http://localhost:8000

User Roles

Manager
- Create projects
- Create tasks
- Assign tasks
- Edit and delete tasks
- View all dashboards

 Employee
- View assigned tasks
- Update task status
- Manage profile

 Project Structure
apps/
config/
tasks/
templates/
static/
assets/

 Deployment
Supports:
- Docker Compose
- Render
- Railway
- Heroku

 Testing
make test

 License
MIT

Author
Saheel Amir Haroon
Copyright
