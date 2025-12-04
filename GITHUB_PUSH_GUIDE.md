# How to Push to GitHub

## Step 1: Create a GitHub Repository

1. Go to https://github.com
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Name it (e.g., "Online-Food-Ordering-System")
5. Choose Public or Private
6. **DO NOT** initialize with README, .gitignore, or license (we already have files)
7. Click "Create repository"

## Step 2: Add and Commit All Files

Run these commands in your terminal:

```bash
# Add all files (except those in .gitignore)
git add .

# Commit the changes
git commit -m "Initial commit: Online Food Ordering System with admin notifications"
```

## Step 3: Connect to GitHub and Push

After creating the repository on GitHub, you'll see instructions. Use these commands:

```bash
# Add the remote repository (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**OR** if you already have a remote configured, just run:
```bash
git push -u origin main
```

## Important Notes:

- The `.env` file is excluded (contains sensitive data)
- Database files (`.db`, `.sqlite`) are excluded
- Python cache files (`__pycache__`) are excluded
- All your code, templates, and static files will be pushed

## If You Get Authentication Errors:

You may need to use a Personal Access Token instead of password:
1. Go to GitHub Settings > Developer settings > Personal access tokens
2. Generate a new token with `repo` permissions
3. Use the token as your password when pushing

