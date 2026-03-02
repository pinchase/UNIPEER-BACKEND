# 🚨 QUICK FIX - Build Failed Error

## Error Message:
```
django.db.utils.OperationalError: (2005, "Unknown server host 'unipeer-db-kagiripeterson8404-unipeer.j.aivencloud.com' (-2)")
==> Build failed 😞
```

---

## ✅ IMMEDIATE FIX (5 minutes)

### Step 1: Update Render Build Settings

Go to your Render dashboard → Your backend service → Settings:

**Build Command:** Change to:
```bash
./build.sh
```

**Start Command:** Change to:
```bash
./start.sh
```

Click **"Save Changes"**

---

### Step 2: Switch to Render PostgreSQL (Recommended)

#### A. Create PostgreSQL Database:
1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Name: `unipeer-db`
3. Database Name: `unipeer`
4. User: `unipeer_user`
5. Region: Same as your web service
6. Plan: **Free** (or paid)
7. Click **"Create Database"**

#### B. Link Database to Service:
1. Go to your backend service
2. Click **"Environment"** tab
3. Find or add variable: `DATABASE_URL`
4. Click **"Link to Database"**
5. Select your `unipeer-db` database
6. Click **"Save"**

---

### Step 3: Deploy

Click **"Manual Deploy"** → **"Deploy latest commit"**

---

## ✅ Alternative: Keep Aiven MySQL

If you want to keep using Aiven:

### In Render Dashboard → Environment:

1. **Rename variable** from `DB_URL` to `DATABASE_URL`
2. Ensure the value is a full connection string:
   ```
   mysql://username:password@unipeer-db-kagiripeterson8404-unipeer.j.aivencloud.com:PORT/database
   ```
3. **Add to requirements.txt:**
   ```
   mysqlclient>=2.2.1
   ```
4. Update Build Command to: `./build.sh`
5. Update Start Command to: `./start.sh`
6. Deploy

---

## 🔍 What Was Wrong?

**Problem:** Django tried to connect to the database **during the build phase**, but:
- Build environment can't access external databases
- DNS resolution fails for Aiven hostname during build
- Migrations tried to run before database was available

**Solution:**
- ✅ `build.sh` - Runs during build (no DB connection)
- ✅ `start.sh` - Runs on startup (DB is available)
- ✅ Fixed settings.py to handle missing DATABASE_URL gracefully

---

## 📋 Quick Verification

After redeploying, check:

1. **Build Logs** should show:
   ```
   ✅ Build completed successfully!
   ```

2. **Runtime Logs** should show:
   ```
   🔄 Running database migrations...
   🚀 Starting Gunicorn server...
   ```

3. **Test endpoint:**
   ```bash
   curl https://your-app.onrender.com/api/stats/
   ```
   Should return JSON data.

---

## 🆘 Still Failing?

### Check These:

1. **Files exist in your repo:**
   - `build.sh` (should be executable)
   - `start.sh` (should be executable)

2. **Commit and push them:**
   ```bash
   git add build.sh start.sh render.yaml requirements.txt
   git commit -m "fix: Add build and start scripts for Render deployment"
   git push origin main
   ```

3. **In Render, trigger redeploy:**
   - Manual Deploy → Deploy latest commit

---

## 📞 Need More Help?

See full guide: `RENDER_DEPLOYMENT_GUIDE.md`

---

**Expected Result:** ✅ Build succeeds → Service starts → API is live!

