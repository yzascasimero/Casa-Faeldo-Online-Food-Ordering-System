# How to Run the Online Food Ordering System

## Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

## Step 1: Install Dependencies

Open a terminal/command prompt in the project directory and run:

```bash
pip install -r requirements.txt
```

Or if you're using Python 3 specifically:

```bash
python -m pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

Create a `.env` file in the project root directory with the following content:

```
SECRET_KEY=your-secret-key-here-change-this-in-production
DATABASE_URL=sqlite:///food_ordering.db
```

**Note:** 
- Replace `your-secret-key-here-change-this-in-production` with a random secret string (you can generate one using Python: `python -c "import secrets; print(secrets.token_hex(32))"`)
- The `DATABASE_URL` uses SQLite by default. For production, you might want to use MySQL or PostgreSQL.

## Step 3: Initialize the Database

Run the following command to create the database tables and create a default admin user:

```bash
flask init-db
```

Or if using Python directly:

```bash
python -c "from app import app, db; app.app_context().push(); from models import Admin; db.create_all(); admin = Admin(username='admin'); admin.set_password('password'); db.session.add(admin); db.session.commit(); print('Database initialized!')"
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `password`

**⚠️ IMPORTANT:** Change the admin password after first login!

## Step 4: Run the Application

Run the Flask application:

```bash
python app.py
```

Or using Flask CLI:

```bash
flask run
```

The application will start and you should see output like:
```
 * Running on http://127.0.0.1:5000
```

## Step 5: Access the Application

1. **Customer Interface:** Open your browser and go to `http://localhost:5000` or `http://127.0.0.1:5000`

2. **Admin Dashboard:** Go to `http://localhost:5000/admin/login`
   - Username: `admin`
   - Password: `password`

## Troubleshooting

### If you get "Module not found" errors:
- Make sure you've installed all dependencies: `pip install -r requirements.txt`
- Check that you're using the correct Python version

### If you get database errors:
- Make sure you've run the `init-db` command
- Check that the `.env` file exists and has the correct `DATABASE_URL`

### If the port is already in use:
- Change the port by running: `flask run --port 5001`
- Or modify `app.py` to use a different port

## Development Mode

The app runs in debug mode by default (as seen in `app.py`). For production, set:
```python
app.run(debug=False)
```

## Additional Notes

- The database file (`food_ordering.db`) will be created in the project root directory
- Static files (images, CSS, JS) are in the `static/` folder
- Templates are in the `templates/` folder
- Uploaded product images will be stored in `static/uploads/`





