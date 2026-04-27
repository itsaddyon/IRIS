# IRIS GitHub Setup

## Step 1 — Go to github.com → New Repository
- Name: `iris-pothole-detection`
- Description: `AI-powered pothole detection and municipal alert system`
- Public ✅
- Do NOT initialize with README (we have our own)
- Click Create Repository

## Step 2 — Open terminal in IRIS folder
```
cd "D:\Btech Projects\IRIS"
```

## Step 3 — Initialize and push
```
git init
git add .
git commit -m "IRIS v1.0 - Intelligent Road Inspection System"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/iris-pothole-detection.git
git push -u origin main
```
Replace YOUR_USERNAME with your GitHub username.

## Step 4 — Add model weights (best.pt is excluded by .gitignore)
Since best.pt is 6MB, share it via Google Drive link in your README.
Add this line to README.md:
> Download model weights: [best.pt](YOUR_GDRIVE_LINK)

## Live Demo Link
IRIS runs locally so there's no hosted live link unless you deploy it.
For Technomax demo just run python main.py and show localhost:5000.
If you want a live link, deploy to Railway.app (free):
1. Go to railway.app → New Project → Deploy from GitHub
2. Select iris-pothole-detection repo
3. Set start command: python main.py
4. Railway gives you a live URL like iris-production.up.railway.app
