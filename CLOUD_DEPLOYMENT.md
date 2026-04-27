# IRIS Cloud Deployment Guide
## Google Cloud Run + Gemini AI

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   IRIS on Cloud Run                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Flask Web App + SocketIO                              │
│  ├─ /dashboard  (Real-time incident monitoring)        │
│  ├─ /municipal  (Municipal admin panel)                │
│  └─ /api/*      (REST endpoints)                       │
│                                                          │
│  Detection Engine (Background)                         │
│  ├─ YOLO-based traffic incident detection             │
│  ├─ Google Gemini AI analysis (Incident insights)     │
│  └─ Real-time WebSocket updates                       │
│                                                          │
├─────────────────────────────────────────────────────────┤
│              Google Cloud Services                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  • Cloud Run      - Serverless app hosting             │
│  • Cloud Storage  - Incident snapshots & data          │
│  • Firestore      - Real-time incident database        │
│  • Gemini API     - AI-powered incident analysis      │
│  • Secret Manager - API keys & credentials            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
3. **Docker** installed (for local testing): https://docker.com
4. **Gemini API Key**: Get free key at https://aistudio.google.com/apikey
5. **Project ready**: IRIS code committed to repository

---

## Step 1: Set Up Google Cloud Project

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Create a new project
gcloud projects create iris-traffic-ai --set-as-default

# Set project ID
export PROJECT_ID=iris-traffic-ai
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  generativeai.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com
```

---

## Step 2: Set Up Gemini API Key

```bash
# Get your Gemini API key from:
# https://aistudio.google.com/apikey

# Store as Secret Manager secret
echo "YOUR_GEMINI_API_KEY_HERE" | gcloud secrets create gemini-api-key --data-file=-

# Grant Cloud Run service account access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member=serviceAccount:iris-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

---

## Step 3: Prepare Application for Cloud Run

### Update app.py for Cloud Run

```python
# At the top of web/app.py, add:

import os
import logging

# Configure logging for Cloud Run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cloud Run passes PORT as environment variable
FLASK_PORT = int(os.environ.get('PORT', 8080))

# ── Update Flask app configuration
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### Update config.py for Cloud Runtime

```python
# Add at end of config.py:

# ─── Cloud Run Environment ───────────────────────────────
IS_CLOUD_RUN = os.environ.get('K_SERVICE') is not None

if IS_CLOUD_RUN:
    # Use Cloud Storage for snapshots
    SNAPSHOTS_DIR = '/tmp/snapshots'  # Ephemeral storage
    # In production, use Cloud Storage:
    # from google.cloud import storage
    # SNAPSHOTS_BUCKET = os.environ.get('SNAPSHOTS_BUCKET', 'iris-snapshots')
    
    # Use Firestore instead of SQLite
    # DB_PATH = 'firestore'  # Custom flag to switch DB backends
    
    # API URLs for cloud-hosted services
    FLASK_PORT = int(os.environ.get('PORT', 8080))
    DEBUG = False
```

---

## Step 4: Build & Deploy to Cloud Run

### Option A: Direct Deploy (Recommended for Quick Testing)

```bash
# Build Docker image
docker build -t gcr.io/$PROJECT_ID/iris:latest .

# Deploy to Cloud Run
gcloud run deploy iris \
  --image gcr.io/$PROJECT_ID/iris:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --set-env-vars="GEMINI_API_KEY=\$(gcloud secrets versions access latest --secret=gemini-api-key)" \
  --allow-unauthenticated
```

### Option B: Using Cloud Build (CI/CD)

```bash
# Create cloudbuild.yaml (auto-triggered on git push)
cat > cloudbuild.yaml << 'EOF'
steps:
  # Build image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/iris:$SHORT_SHA', '.']
  
  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/iris:$SHORT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
      - run
      - --filename=.
      - --image=gcr.io/$PROJECT_ID/iris:$SHORT_SHA
      - --location=us-central1
      - --output=/workspace/output

images:
  - 'gcr.io/$PROJECT_ID/iris:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/iris:latest'
EOF

# Push code to Cloud Source Repository
git push origin main  # Triggers automatic build & deploy
```

---

## Step 5: Cloud Storage for Incident Snapshots

```bash
# Create storage bucket
gsutil mb gs://iris-snapshots-$PROJECT_ID

# Set permissions
gsutil iam ch \
  serviceAccount:iris-sa@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectViewer \
  gs://iris-snapshots-$PROJECT_ID

gsutil iam ch \
  serviceAccount:iris-sa@$PROJECT_ID.iam.gserviceaccount.com:roles/storage.objectCreator \
  gs://iris-snapshots-$PROJECT_ID
```

### Update code to use Cloud Storage:

```python
# In main.py, replace snapshot saving:

from google.cloud import storage
import io

def save_snapshot_to_cloud(frame):
    """Save detection snapshot to Google Cloud Storage."""
    try:
        client = storage.Client()
        bucket = client.bucket(os.environ.get('SNAPSHOTS_BUCKET'))
        
        fname = f"High_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.jpg"
        blob = bucket.blob(f"snapshots/{fname}")
        
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        blob.upload_from_string(buffer.tobytes(), content_type='image/jpeg')
        
        return f"gs://iris-snapshots-{os.environ.get('PROJECT_ID')}/snapshots/{fname}"
    except Exception as e:
        logger.error(f"Cloud storage failed: {e}")
        return None
```

---

## Step 6: View Deployment

```bash
# Get Cloud Run service URL
gcloud run services describe iris --region us-central1 --format='value(status.url)'

# View logs in real-time
gcloud run logs read iris --limit 100 --region us-central1 --follow

# Check service status
gcloud run services describe iris --region us-central1
```

---

## Step 7: Monitor & Debug

### Cloud Monitoring Dashboard

```bash
# Create monitoring dashboard
gcloud monitoring dashboards create --config-from-file=- << 'EOF'
{
  "displayName": "IRIS Traffic Monitoring",
  "dashboardFilters": [],
  "gridLayout": {
    "widgets": [
      {
        "title": "Cloud Run Service",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\""
              }
            }
          }]
        }
      }
    ]
  }
}
EOF
```

### View Error Logs

```bash
# Search for errors
gcloud logging read "resource.type=cloud_run_revision AND severity=ERROR" \
  --limit 50 \
  --region us-central1 \
  --format=json
```

---

## Step 8: Environment Variables & Secrets

```bash
# Store in Secret Manager (not in code!)
gcloud secrets create db-password --data-file=- << 'EOF'
your_secure_password_here
EOF

# Reference in Cloud Run deployment
gcloud run deploy iris \
  --set-env-vars=\
"GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key),\
FLASK_ENV=production,\
SNAPSHOTS_BUCKET=iris-snapshots-$PROJECT_ID"
```

---

## Step 9: Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service=iris \
  --domain=iris.yourdomain.com \
  --region=us-central1

# Verify DNS records and SSL certificate are created automatically
```

---

## Costs & Billing

**Estimated Monthly Costs (Low Traffic):**
- Cloud Run: ~$0-5 (always free tier: 2M requests/month)
- Cloud Storage: ~$0.02-1 (snapshot storage)
- Firestore: ~$0-1 (read/write operations)
- Gemini API: ~$0.005-5 (based on usage)
- **Total: ~$5-15/month for pilot**

**To minimize costs:**
- Use Cloud Run's always-free tier
- Archive old snapshots to cheaper storage classes
- Use Firestore's auto-scaling
- Monitor Gemini API usage

---

## Troubleshooting

### Issue: "Permission denied" accessing Gemini API

```bash
# Check service account has access to secret
gcloud secrets get-iam-policy gemini-api-key

# Grant access if needed
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member=serviceAccount:iris-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

### Issue: Container fails to start

```bash
# Test build locally
docker build -t iris:test .
docker run -e PORT=8080 iris:test

# Check Cloud Run logs
gcloud run logs read iris --limit 100 --follow
```

### Issue: Gemini API timeout

- Increase Cloud Run timeout: `--timeout 3600`
- Use async processing for AI analysis
- Implement caching for repeated queries

---

## Next Steps for Production

1. **Firestore Integration**: Replace SQLite with Firestore for distributed DB
2. **Load Balancing**: Set up Cloud CDN for faster delivery
3. **Alerts**: Configure Cloud Monitoring alerts for high-severity incidents
4. **Auto-scaling**: Adjust memory/CPU based on traffic patterns
5. **Security**: Enable VPC, IAM policies, and Cloud Armor

---

## Hackathon Submission Checklist

✅ **Google AI Integration**: Gemini API for intelligent incident analysis
✅ **Cloud Deployment**: Cloud Run for serverless hosting
✅ **Real-time Updates**: WebSocket integration via SocketIO
✅ **Incident Snapshots**: Cloud Storage for evidence
✅ **Monitoring**: Cloud Monitoring & Logging

**Deployment URL**: [Your Cloud Run URL]
**Live Demo**: Access at https://iris-[project-id].run.app

---

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Gemini API Guide](https://ai.google.dev/docs)
- [Cloud Storage Quickstart](https://cloud.google.com/storage/docs/quickstart-console)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
