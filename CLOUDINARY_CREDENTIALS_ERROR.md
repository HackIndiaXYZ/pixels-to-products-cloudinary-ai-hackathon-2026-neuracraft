# Cloudinary 401 Error - Troubleshooting Guide

## Root Cause

The Cloudinary API returns a 401 when the API credentials in `backend/.env` are
incorrect or do not match the Cloudinary account.

```json
{"error":{"message":"api_secret mismatch"}}
```

## Solution

1. Log in to your Cloudinary dashboard: https://cloudinary.com/console
2. Navigate to **Settings → Access Keys** (or the Dashboard product credentials section).
3. Copy the three values:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

4. Update `backend/.env`:

```bash
CLOUDINARY_CLOUD_NAME=<your_cloud_name>
CLOUDINARY_API_KEY=<your_api_key>
CLOUDINARY_API_SECRET=<your_api_secret>
```

5. Restart the backend server.

## Verification

```bash
cd backend
python -c "
import requests
url = 'https://api.cloudinary.com/v1_1/<CLOUD_NAME>/usage'
auth = ('<API_KEY>', '<API_SECRET>')
response = requests.get(url, auth=auth)
print('Status:', response.status_code)
print('Valid credentials' if response.status_code == 200 else response.text)
"
```

## Security Reminder

- Never commit `backend/.env` to source control.
- Never share the API secret publicly.
- Use `.env.example` as the template (no real values).
