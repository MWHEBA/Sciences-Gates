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

## Updating Majors Database (Best & Cheap Universities)
To safely populate the missing `best_universities` and `cheap_universities` relationships in production:

1. **Backup MySQL Database (Crucial)**:
   - Log in to your cPanel dashboard.
   - Go to **phpMyAdmin** or **Backup Wizard**.
   - Select your production database and click **Export** to save a `.sql` backup file locally before making any changes.

2. **Deploy the custom command**:
   - Ensure the new command file [populate_missing_universities.py](file:///c:/Users/MohYousif/Desktop/Sciences%20Gates/apps/majors/management/commands/populate_missing_universities.py) is uploaded to the production directory.

3. **Execute the update**:
   - Run the simulation first on the production server (via SSH or the cPanel terminal/cron utility) to verify the records:
     ```bash
     python manage.py populate_missing_universities --dry-run
     ```
   - If the output completes successfully, run the actual commit to update the production database:
     ```bash
     python manage.py populate_missing_universities --commit
     ```

