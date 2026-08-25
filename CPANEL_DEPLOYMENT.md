# cPanel Deployment Guide

This guide documents the steps and configuration required to deploy the Science Gates portal on a cPanel hosting environment.

## Prerequisites
- cPanel access with Python Setup App enabled.
- MySQL database and user created.
- Domain name pointed to the hosting.

## Deployment Steps
1. Upload the files to the root directory.
2. Setup the Python Application in cPanel.
3. Configure the environment variables.
4. Run migrations.
5. Collect static files.
6. Verify and set up SSL.

## Python Application
- Select Python version (3.11 recommended).
- Application root: `public_html` or the project directory.
- Application URL: the main domain.
- Passenger WSGI file: `passenger_wsgi.py`.

## MySQL Database
- Create a MySQL Database.
- Create a Database User and grant all privileges.
- Configure DB settings in the `.env` file.

## Environment Variables
Create a `.env` file in the application root with:
- `DEBUG=False`
- `SECRET_KEY=your_secret_key`
- `ALLOWED_HOSTS=yourdomain.com`
- `DB_NAME=database_name`
- `DB_USER=database_user`
- `DB_PASSWORD=database_password`
- `DB_HOST=127.0.0.1`
- `DB_PORT=3306`

## Static Files
Run `python manage.py collectstatic --noinput` to collect all static files into `staticfiles`.

## SSL Certificate
Ensure Let's Encrypt or another SSL Certificate is generated and activated on cPanel.
