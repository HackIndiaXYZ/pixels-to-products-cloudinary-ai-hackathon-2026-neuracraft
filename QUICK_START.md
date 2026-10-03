# CreativePulse AI - Quick Start Guide

## ✅ Both servers are running!

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 🔐 Login Required

The navigation sidebar requires authentication. To access the dashboard:

### Demo Account (Ready to Use)
- **Email:** demo@creativepulse.ai
- **Password:** demo123

### Steps to Login:
1. Navigate to http://localhost:3000/login
2. Enter the demo credentials above
3. Click "Sign In"
4. You'll be redirected to the dashboard where all navigation links will work!

### Existing Users
The database also has these accounts:
- shashimogaveera7@gmail.com
- test@example.com
- amashritha40@gmail.com
- ashrithaam8@gmail.com

(If you know the passwords for any of these, you can use them too)

## 📱 What You Can Do After Login

Once logged in, you'll have access to:
- **Overview** - Campaign metrics and insights dashboard
- **New Analysis** - Create a new creative analysis
- **Creative Library** - Browse your creative assets
- **Creative DNA** - Visual pattern intelligence
- **Performance** - Campaign performance data
- **Repurpose** - Transform creative formats (requires Cloudinary setup)
- **AI Assistant** - Ask questions about your data
- **Reports** - Export and share insights
- **Settings** - Account and preferences

### 🧪 Test Navigation
If navigation seems unresponsive, visit: http://localhost:3000/test-nav
This diagnostic page will help identify any navigation issues.

## 🔧 Technical Notes

- Using SQLite database (creativepulse_test.db)
- Cloudinary is not configured (optional for testing)
- Both servers auto-reload on code changes
- JWT tokens stored in browser localStorage

## 🛑 To Stop the Servers

The servers are running in background processes. You can stop them via Kiro or by pressing Ctrl+C in their respective terminals.

---

Happy analyzing! 🎨✨
