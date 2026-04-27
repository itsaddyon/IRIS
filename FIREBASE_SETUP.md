# IRIS Firebase Setup Guide
## Easy Cloud Deployment (No Docker, No Complex Build)

### Why Firebase Instead of Cloud Run?
- ✅ **Simpler**: 5 minutes setup
- ✅ **Faster**: No build failures
- ✅ **Free**: Generous free tier
- ✅ **Live URL**: Public dashboard
- ✅ **Global Data**: Firestore database

---

## **Step 1: Install Firebase Tools**

```bash
npm install -g firebase-tools
```

Then verify:
```bash
firebase --version
```

---

## **Step 2: Create Firebase Project**

### Option A: Use Existing Google Cloud Project
```bash
# Link to your existing project
gcloud config get-value project

# Should show: gen-lang-client-0246100100
```

### Option B: Go to Firebase Console
1. Visit: https://console.firebase.google.com/
2. Click **"Add project"**
3. Select your existing GCP project
4. Enable: Firestore, Hosting, Authentication

---

## **Step 3: Login to Firebase**

```bash
firebase login
```

Browser opens → Sign in with your Google account

---

## **Step 4: Initialize Firebase in IRIS Folder**

```bash
cd d:\Btech Projects\IRIS
firebase init
```

When prompted, answer:
```
? Which Firebase features would you like to set up?
  ✓ Firestore Database
  ✓ Hosting

? Use an existing project?
  ✓ Yes

? Which project?
  ✓ gen-lang-client-0246100100 (your GCP project)

? What file should be used for Firestore indexes?
  ✓ firestore.indexes.json (press enter)

? What file should be used for Firestore rules?
  ✓ firestore.rules (press enter)

? What directory should be used for public files?
  ✓ web/templates (or just press enter)
```

---

## **Step 5: Install Python Firebase Package**

```bash
pip install firebase-admin
```

---

## **Step 6: Get Service Account Key**

This allows your code to write to Firestore:

1. Go to: https://console.cloud.google.com/
2. Select your project
3. **IAM & Admin** → **Service Accounts**
4. Click **"Create Service Account"**
   - Name: `iris-app`
   - Click Create
5. Click on the account you just created
6. **Keys** tab → **Add Key** → **Create New Key**
7. Choose **JSON**
8. **Save** the JSON file to your IRIS folder as: `firestore-key.json`

---

## **Step 7: Update main.py to Use Service Key**

In `main.py`, update the Firestore initialization:

```python
# Replace this:
# firebase_admin.initialize_app()

# With this:
firebase_admin.initialize_app(credentials.Certificate('firestore-key.json'))
```

---

## **Step 8: Create Firestore Database**

1. Go to: https://console.firebase.google.com/
2. Select your project
3. **Firestore Database** (left menu)
4. Click **Create Database**
   - Start in **Production mode**
   - Region: **us-central1**
   - Click **Create**

---

## **Step 9: Set Firestore Security Rules**

Replace `firestore.rules` content with:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /detections/{document=**} {
      allow read, write: if true;
    }
  }
}
```

Deploy:
```bash
firebase deploy --only firestore:rules
```

---

## **Step 10: Test Locally**

```bash
pip install -r requirements.txt
python main.py
```

When you detect a pothole:
- ✅ Local dashboard updates
- ✅ Gemini analyzes it
- ✅ **Data saves to Firestore** (check console for ✓ message)

---

## **Step 11: Deploy Hosting (Get Live URL)**

```bash
firebase deploy --only hosting
```

You'll get:
```
Hosting URL: https://your-project.web.app
```

---

## **Step 12: View Live Data**

Create a simple HTML dashboard to view Firestore data:

**File**: `web/templates/firebase-dashboard.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>IRIS - Firestore Dashboard</title>
    <script src="https://www.gstatic.com/firebasejs/9.0.0/firebase-app.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.0.0/firebase-firestore.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #f5f5f5; }
        .detection { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .high { border-left: 4px solid red; }
        .medium { border-left: 4px solid orange; }
        .low { border-left: 4px solid yellow; }
    </style>
</head>
<body>
    <h1>🚨 IRIS Pothole Detections</h1>
    <div id="detections"></div>

    <script>
        const firebaseConfig = {
            // Copy from your Firebase Console → Project Settings
            apiKey: "YOUR_API_KEY",
            projectId: "your-project-id",
            appId: "your-app-id"
        };

        firebase.initializeApp(firebaseConfig);
        const db = firebase.firestore();

        db.collection('detections')
            .orderBy('timestamp', 'desc')
            .limit(50)
            .onSnapshot(snapshot => {
                document.getElementById('detections').innerHTML = '';
                snapshot.forEach(doc => {
                    const data = doc.data();
                    const html = `
                        <div class="detection ${data.severity.toLowerCase()}">
                            <strong>${data.severity}</strong> - ${data.location || 'Unknown'}
                            <br><small>${data.timestamp}</small>
                            <br>Confidence: ${(data.confidence * 100).toFixed(0)}%
                            <br><em>${data.recommended_action}</em>
                        </div>
                    `;
                    document.getElementById('detections').innerHTML += html;
                });
            });
    </script>
</body>
</html>
```

---

## **Complete Architecture Now**

```
Your Computer (Local)
├─ Camera + Arduino
├─ YOLO Detection
├─ Gemini Analysis
└─ Save to Firestore
       ↓
Firebase (Cloud)
├─ Firestore Database (Global Data)
├─ Hosting (Live Dashboard)
└─ Public URL: https://iris-project.web.app
       ↓
Accessible Worldwide
```

---

## **What You Have Now**

✅ **Priority 1**: Gemini AI working locally
✅ **Priority 2**: Live URL (Firebase Hosting)
✅ **Priority 3**: Global data storage (Firestore)

---

## **Hackathon Submission**

You can now show judges:

1. **Local Demo**: Camera detecting potholes + Arduino alerts
2. **Cloud Dashboard**: https://iris-project.web.app (live data)
3. **Pitch**: "IRIS uses Google Gemini for AI analysis and Firebase for global data storage"

---

## **Troubleshooting**

### "Firestore not initialized"
- Make sure `firestore-key.json` is in your IRIS folder
- Check file permissions
- Verify the service account has Firestore access

### "Data not saving to Firestore"
- Check console output for `✓ Saved to Firestore` message
- Verify Firestore security rules allow writes
- Check Firestore console for any errors

### "Can't connect to Firebase"
- Verify `firebase login` successful
- Check internet connection
- Verify project ID is correct

---

## **Next Steps**

After getting this working:
1. Add more analysis fields to Firestore
2. Create charts/maps for pothole locations
3. Add alerts/notifications
4. Export reports

---

**Ready? Start with Step 1!** 🚀
