# 🚨 CORS & 500 Error Explanation

## The Error You're Seeing

```
Access to fetch at 'https://unipeer-backend.onrender.com/api/register/' 
from origin 'https://unipeer-frontend-qarwk323y-peterson-murayas-projects.vercel.app' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.

POST https://unipeer-backend.onrender.com/api/register/ net::ERR_FAILED 500 (Internal Server Error)

API Error: TypeError: Failed to fetch
```

---

## 🔍 What's Happening (Two Problems)

### Problem 1: CORS Error (Frontend Can't Connect)

**What You See:**
```
No 'Access-Control-Allow-Origin' header is present
```

**What This Means:**
Your backend is NOT sending the CORS header that allows your Vercel preview URL to access it.

**Why It's Happening:**

Looking at your `settings.py`:

```python
# Line 186-191
def get_allowed_origins():
    origins = [
        "https://unipeer-frontend.vercel.app",  # ✅ Production URL
        "http://localhost:3000",                # ✅ Local dev
        "http://127.0.0.1:3000",                # ✅ Local dev
    ]
    return origins

CORS_ALLOWED_ORIGINS = get_allowed_origins()

# Line 195-199
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",  # ✅ Should match ALL Vercel URLs
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
]
```

**The Configuration Looks Correct!** 

Your regex `r"^https://.*\.vercel\.app$"` SHOULD match:
```
https://unipeer-frontend-qarwk323y-peterson-murayas-projects.vercel.app
```

**So Why Is It Not Working?**

There are 3 possible reasons:

#### Reason A: The 500 Error Happens BEFORE CORS Headers Are Added
When your backend crashes with a 500 error, Django might not reach the middleware that adds CORS headers. The error happens early in the request processing.

**The Flow:**
```
1. Request arrives at backend
2. Django starts processing
3. ❌ CRASH (500 error in RegisterView)
4. Error response sent WITHOUT CORS headers
5. Browser blocks the response (CORS error)
```

#### Reason B: RegisterView Is Missing `permission_classes = [AllowAny]`
Looking at your code:
```python
class RegisterView(APIView):
    """Register a new student and create their profile."""
    # ❌ MISSING: permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = StudentProfileCreateSerializer(data=request.data)
        # ...
```

**Without `AllowAny`, the view uses the default permission from settings:**
```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"  # ← Requires auth!
    ],
}
```

**This means:**
- RegisterView requires authentication BY DEFAULT
- New users can't register because they need to be authenticated first
- This causes a 403 or 500 error BEFORE CORS headers are added

#### Reason C: Backend Crashed During Deployment
If your backend isn't running properly on Render, it might be returning 500 errors for all requests.

---

### Problem 2: 500 Internal Server Error (Backend Crash)

**What You See:**
```
POST https://unipeer-backend.onrender.com/api/register/ 
net::ERR_FAILED 500 (Internal Server Error)
```

**What This Means:**
Your backend code is crashing when processing the registration request.

**Likely Causes:**

#### Cause 1: Database Not Connected
If `DATABASE_URL` isn't set or the database isn't running:
```python
# In RegisterView.post():
serializer.save()  # ← Tries to write to database
# If DB not connected → 500 error
```

#### Cause 2: Missing Fields in Request
If the frontend is sending incomplete data:
```python
StudentProfileCreateSerializer(data=request.data)
# If required fields missing → ValidationError → 500
```

#### Cause 3: Serializer Issues
The serializer might be failing:
```python
# In StudentProfileCreateSerializer
def create(self, validated_data):
    # If this crashes → 500 error
```

#### Cause 4: CSRF Token Issues
Even though REST API shouldn't need CSRF, settings might be enforcing it:
```python
CSRF_COOKIE_SECURE = not DEBUG  # True in production
CSRF_COOKIE_HTTPONLY = True
```

---

## 🔍 The Complete Error Flow

Here's what's actually happening:

```
1. Frontend (Vercel Preview URL): Makes POST request to /api/register/

2. Browser: Sends preflight OPTIONS request first
   ↓
   Backend: Should respond with CORS headers
   ↓
   ✅ If CORS OK: Browser proceeds with POST request
   ❌ If CORS fails: Browser blocks request

3. Backend Receives POST Request:
   ↓
   Django Middleware Chain:
   - SecurityMiddleware ✅
   - CorsMiddleware ✅ (adds headers)
   - SessionMiddleware ✅
   - CsrfViewMiddleware ⚠️ (might check CSRF token)
   - AuthenticationMiddleware ⚠️ (checks authentication)
   
4. View Processing (RegisterView):
   ↓
   Permission Check:
   - ❌ If IsAuthenticated required → 403/401 error
   - ✅ If AllowAny → Continue
   
5. Serializer Validation:
   ↓
   - Validate request data
   - ❌ If validation fails → 400 error
   - ❌ If serializer crashes → 500 error
   
6. Database Write:
   ↓
   - Create User
   - Create StudentProfile
   - ❌ If DB not connected → 500 error
   - ❌ If constraint violation → 500 error
   
7. Response:
   ↓
   If error occurred before CORS headers added:
   - Response has NO CORS headers
   - Browser blocks response
   - You see CORS error + 500 error
```

---

## 🎯 Diagnosis: What's Actually Wrong

Based on your error, here's what I believe is happening:

### Most Likely Issue: RegisterView Missing AllowAny

**In your current code:**
```python
class RegisterView(APIView):
    """Register a new student and create their profile."""
    # ❌ MISSING: permission_classes = [AllowAny]
```

**What happens:**
1. Request arrives
2. Django checks authentication (DEFAULT: IsAuthenticated)
3. User is not authenticated (they're trying to register!)
4. Django returns 403 Forbidden or crashes trying to check auth
5. Error response doesn't have CORS headers
6. Browser shows CORS error

### Second Most Likely: Backend Database Issue

If the backend deployment has issues:
- Database not connected (DATABASE_URL not set)
- Migrations not run (tables don't exist)
- Backend service crashed/not running

---

## 🔧 How to Diagnose Further (Without Code Changes)

### Step 1: Check Render Backend Logs

Go to Render Dashboard → Your Backend Service → Logs

**Look for:**
```
# Good signs:
🚀 Starting Gunicorn server...
[INFO] Listening at: http://0.0.0.0:3000

# Bad signs:
❌ OperationalError: could not connect to database
❌ ImproperlyConfigured: ...
❌ ModuleNotFoundError: ...
❌ 500 Internal Server Error
❌ Traceback (most recent call last):
```

**If you see database errors:**
- DATABASE_URL not set
- Database not created
- Migrations not run

**If you see import errors:**
- Dependencies not installed
- Code syntax errors

### Step 2: Test Backend Directly (Bypass CORS)

Open a terminal and test the backend directly:

```bash
# Test if backend is alive
curl https://unipeer-backend.onrender.com/api/stats/

# Expected: JSON response with stats
# If fails: Backend is down
```

```bash
# Test registration endpoint
curl -X POST https://unipeer-backend.onrender.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Expected: User created OR validation error
# If you get: 500 error → Backend code issue
# If you get: Authentication required → Missing AllowAny
# If you get: HTML error page → Backend crashed badly
```

### Step 3: Check CORS Headers (When Backend Works)

```bash
# Test CORS preflight
curl -X OPTIONS https://unipeer-backend.onrender.com/api/register/ \
  -H "Origin: https://unipeer-frontend-qarwk323y-peterson-murayas-projects.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Look for in response headers:
# Access-Control-Allow-Origin: *
# OR
# Access-Control-Allow-Origin: https://unipeer-frontend-qarwk323y...
```

**If you DON'T see these headers:**
- CORS middleware not working
- Backend crashed before CORS middleware runs
- CORS configuration issue

### Step 4: Check Environment Variables

In Render Dashboard → Environment:

**Required variables:**
```
✅ DATABASE_URL - Set and linked to database
✅ SECRET_KEY - Set
✅ DEBUG - Set to False
✅ ALLOWED_HOSTS - Includes .onrender.com
```

---

## 📊 The Verdict

Without seeing the backend logs, here's my diagnosis:

**Primary Issue (90% certain):**
```python
# RegisterView is missing:
permission_classes = [AllowAny]

# This causes authentication check to fail
# Which results in 500/403 error
# Which happens before CORS headers are added
# Which makes browser show CORS error
```

**Secondary Issues (Possible):**
1. Database not connected (DATABASE_URL issue)
2. Migrations not run (tables don't exist)
3. Backend service not running properly
4. Serializer validation failing

---

## 🎯 Root Cause Summary

### The CORS Error is a RED HERRING!

**The real problem is the 500 error.**

The CORS error appears because:
1. Backend crashes (500 error)
2. Crash happens before CORS middleware completes
3. Error response has no CORS headers
4. Browser blocks the response
5. You see CORS error first, then 500 error

**It's like:**
- You call someone on the phone
- The phone rings but they don't answer (500 error)
- You then realize you're calling from a blocked number (CORS)
- But the real problem is they're not answering (500)

### The 500 Error Root Cause:

**Most Likely:**
```python
class RegisterView(APIView):
    # ❌ Missing: permission_classes = [AllowAny]
    # Backend tries to authenticate non-authenticated user
    # Crashes or returns error
    # CORS headers not added to error response
```

**Also Check:**
- Backend logs for actual error traceback
- Database connection status
- Environment variables
- Migration status

---

## 📝 Next Steps (Without Code Changes)

1. **Check Render Logs** (Most Important!)
   - Go to Render → Backend Service → Logs
   - Look for the actual error when register is called
   - Share the error traceback

2. **Test Backend Directly**
   - Use curl commands above
   - See if backend responds at all
   - Check if registration works via curl

3. **Verify Environment Variables**
   - Ensure DATABASE_URL is set
   - Ensure backend is actually running

4. **Check Database**
   - Verify database exists
   - Verify migrations ran
   - Check database has tables

---

## 🔑 Key Takeaway

**You're seeing TWO errors:**
1. **CORS error** - "No Access-Control-Allow-Origin header"
2. **500 error** - "Internal Server Error"

**The 500 error is the PRIMARY problem.**
**The CORS error is a SYMPTOM of the 500 error.**

Fix the 500 error (check backend logs!), and the CORS error will disappear.

---

## 📞 What to Do Next

**Without changing code:**
1. Share your Render backend logs (from when the error occurs)
2. Run the curl test commands above
3. Check if DATABASE_URL is set in Render environment
4. Verify your backend service is showing "Live" in Render

**This will tell us the exact 500 error, which we can then fix.**

The CORS configuration in your `settings.py` is actually correct - the regex pattern SHOULD work. The issue is that the backend is crashing before it can send the CORS headers.

