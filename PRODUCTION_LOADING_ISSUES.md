# 🐛 PRODUCTION LOADING ISSUES - DIAGNOSTIC GUIDE

## Why Some Things Are Not Loading on Production

After implementing security fixes, you may see some data not loading. This is **EXPECTED** and **GOOD** - it means security is now working! Here's what's happening and how to fix it.

---

## 🔍 Common Issues & Solutions

### Issue 1: "401 Unauthorized" - No Data Loading ⚠️ MOST COMMON

**What You'll See:**
- Frontend shows empty lists or "No data" messages
- Browser console shows: `401 Unauthorized`
- API requests fail silently

**Why This Happens:**
Your API now requires authentication! Before the security fix, anyone could access all endpoints. Now users need to be logged in.

**Fix:**
Ensure your frontend is:
1. ✅ Getting JWT tokens from login/register
2. ✅ Storing tokens (localStorage or cookies)
3. ✅ Sending tokens with every API request

**Frontend Code Example:**
```javascript
// After login, store the token
const response = await fetch('https://backend.com/api/login/', {
  method: 'POST',
  body: JSON.stringify({ email, password }),
});
const data = await response.json();
localStorage.setItem('access_token', data.access);
localStorage.setItem('refresh_token', data.refresh);

// On every API request, include the token
const token = localStorage.getItem('access_token');
const response = await fetch('https://backend.com/api/profiles/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
});
```

**Quick Test:**
```bash
# Without token (should fail)
curl https://your-backend.com/api/profiles/
# Response: {"detail": "Authentication credentials were not provided."}

# With token (should work)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-backend.com/api/profiles/
# Response: [list of profiles]
```

---

### Issue 2: "403 Forbidden" - Can't Edit/Delete

**What You'll See:**
- Can view data but can't edit
- Browser console shows: `403 Forbidden`
- Edit/delete buttons don't work

**Why This Happens:**
You're trying to edit someone else's resource! New permissions check ownership:
- ✅ Can view: Your own and others' profiles/resources
- ❌ Can edit: Only YOUR OWN resources

**Fix:**
Ensure the logged-in user is trying to edit their own resources.

**Check User ID:**
```javascript
// Get current user's profile ID from login response
const currentUserId = userData.profile.id;

// Only allow editing if it's the user's own resource
if (resource.uploaded_by === currentUserId) {
  // Show edit button
}
```

---

### Issue 3: CORS Error - Can't Connect to API

**What You'll See:**
- Browser console shows: `CORS policy: No 'Access-Control-Allow-Origin' header`
- All API requests fail
- Network tab shows failed requests

**Why This Happens:**
Your Vercel preview URL isn't in the allowed origins list.

**Fix Option 1 - Add to Environment Variable (Recommended):**
On Render.com, add environment variable:
```
ADDITIONAL_CORS_ORIGINS=https://your-specific-preview.vercel.app
```

**Fix Option 2 - Already Works:**
The regex pattern `r"^https://.*\.vercel\.app$"` should already allow all `*.vercel.app` domains. If not working:

1. Check the frontend domain in browser console
2. Verify it matches `https://something.vercel.app` format
3. Check Render logs for CORS errors

**Quick Test:**
```bash
curl -i -H "Origin: https://your-frontend.vercel.app" \
  https://your-backend.com/api/stats/

# Look for this header in response:
# Access-Control-Allow-Origin: https://your-frontend.vercel.app
```

---

### Issue 4: "Request was throttled" - Rate Limited

**What You'll See:**
- Error message: "Request was throttled. Expected available in X seconds."
- Requests suddenly stop working
- Happens after many requests

**Why This Happens:**
Rate limiting is now active:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Login attempts: 5/hour

**Fix:**
1. **Short term:** Wait for rate limit to reset
2. **Long term:** Optimize frontend to make fewer requests
   - Cache data in frontend
   - Use pagination
   - Debounce search/filter inputs

**For Development:**
Temporarily increase limits in `settings.py`:
```python
DEFAULT_THROTTLE_RATES = {
    "anon": "1000/hour",    # Increase for dev
    "user": "10000/hour",   # Increase for dev
}
```

---

### Issue 5: Empty Notifications/Messages

**What You'll See:**
- Notifications page shows nothing
- Chat rooms don't load messages
- Even though you know data exists

**Why This Happens:**
New permissions restrict access:
- Notifications: Only recipient can view
- Rooms: Only members can view
- Matches: Only participants can view

**Fix:**
Ensure you're querying with the correct user ID:
```javascript
// WRONG - Don't query all notifications
fetch('/api/notifications/')

// RIGHT - Query for current user
const userId = currentUser.profile.id;
fetch(`/api/notifications/?recipient_id=${userId}`)

// WRONG - Don't query all rooms
fetch('/api/rooms/')

// RIGHT - Query for current user's rooms
fetch(`/api/rooms/?profile_id=${userId}`)
```

---

### Issue 6: Login/Register Not Working

**What You'll See:**
- Login form submits but nothing happens
- Register form submits but fails
- Console shows errors

**Why This Happens:**
These endpoints were **explicitly made public** with `AllowAny`, so they should work. If not:

**Check 1 - Token Response:**
Login should return JWT tokens:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": { "id": 1, "email": "user@example.com", ... }
}
```

**Check 2 - CORS:**
Ensure frontend domain is allowed (see Issue 3)

**Check 3 - Rate Limiting:**
After 5 failed login attempts, you'll be locked out for 1 hour. Use correct credentials or wait.

**Quick Test:**
```bash
# Test registration
curl -X POST https://your-backend.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass123",...}'

# Test login
curl -X POST https://your-backend.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass123"}'
```

---

## 🔧 Debugging Steps

### Step 1: Check Browser Console
Open DevTools (F12) → Console tab
Look for:
- ❌ 401 errors → Need authentication (Issue 1)
- ❌ 403 errors → Need permissions (Issue 2)
- ❌ CORS errors → Need CORS fix (Issue 3)
- ❌ Throttle errors → Rate limited (Issue 4)

### Step 2: Check Network Tab
Open DevTools (F12) → Network tab
Look at failed requests:
- Check request headers (is `Authorization` present?)
- Check response (what error message?)
- Check status code (401, 403, 429, etc.)

### Step 3: Check Backend Logs
On Render.com:
1. Go to your backend service
2. Click "Logs" tab
3. Look for errors around the time of frontend request

### Step 4: Test API Directly
Use curl or Postman to test API endpoints directly:
```bash
# Get a token
TOKEN=$(curl -X POST https://backend.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@test.com","password":"pass"}' \
  | jq -r '.access')

# Test authenticated endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://backend.com/api/profiles/
```

---

## 📋 Frontend Checklist

To fix loading issues, ensure your frontend:

- [ ] Stores JWT tokens after login/register
- [ ] Includes `Authorization: Bearer <token>` header on all API requests
- [ ] Handles 401 errors by redirecting to login
- [ ] Handles 403 errors by showing "unauthorized" message
- [ ] Queries with correct user IDs for filtered endpoints
- [ ] Implements token refresh when access token expires
- [ ] Has error handling for rate limiting
- [ ] Shows loading states while fetching data

---

## 🎯 Quick Fix Template

Here's a complete authentication flow for your frontend:

```javascript
// 1. Login and store tokens
async function login(email, password) {
  const response = await fetch('https://backend.com/api/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }
  throw new Error('Login failed');
}

// 2. Create authenticated fetch wrapper
async function authenticatedFetch(url, options = {}) {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  // Handle token expiration
  if (response.status === 401) {
    // Try to refresh token
    const refreshed = await refreshToken();
    if (refreshed) {
      // Retry request with new token
      return authenticatedFetch(url, options);
    } else {
      // Redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
}

// 3. Refresh token when expired
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  const response = await fetch('https://backend.com/api/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
    return true;
  }
  return false;
}

// 4. Use authenticated fetch everywhere
const data = await authenticatedFetch('https://backend.com/api/profiles/');
const profiles = await data.json();
```

---

## ✅ Verification Checklist

After fixing frontend authentication:

- [ ] Login works and stores tokens
- [ ] Can view list of profiles
- [ ] Can view own profile details
- [ ] Can edit own profile (not others')
- [ ] Can create resources
- [ ] Can view notifications (filtered to current user)
- [ ] Can view rooms (filtered to current user)
- [ ] 401 errors handled gracefully
- [ ] Token refresh works automatically
- [ ] Rate limiting doesn't block normal usage

---

## 🆘 Still Not Working?

If you've tried everything and still have issues:

1. **Share the error**: Check browser console and share the exact error message
2. **Check the request**: Share the Network tab details (URL, headers, response)
3. **Check backend logs**: Share relevant logs from Render
4. **Verify environment**: Are all environment variables set in Render?

Common environment variables needed:
```
SECRET_KEY=<your-secret-key>
DEBUG=False
ALLOWED_HOSTS=<your-backend-domain>
DB_URL=<database-url>
ADDITIONAL_CORS_ORIGINS=<frontend-urls>  # Optional
```

---

**Remember:** These issues are **GOOD SIGNS** - they mean your API is now secure! The fixes are on the frontend side to properly implement authentication.

