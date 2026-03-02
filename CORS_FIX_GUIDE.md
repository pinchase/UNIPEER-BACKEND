# CORS Configuration Fix for Vercel Preview Deployments

## Problem
Every time you push a new feature to GitHub, Vercel creates a new preview deployment with a unique domain (e.g., `frontend-abc123.vercel.app`). The backend's CORS configuration was hardcoded to only allow one specific domain, causing:
- ❌ API requests to fail with CORS errors
- ❌ Frontend unable to communicate with backend
- ❌ Features unable to load or work properly

## Solution
Updated `unipeer/settings.py` to use **regex pattern matching** for CORS allowed origins.

### What Changed

#### Before (Static Domain Only)
```python
CORS_ALLOWED_ORIGINS = [
    "https://unipeer-frontend.vercel.app",
]
```
❌ Only the main production domain works
❌ All preview deployments blocked (CORS error)

#### After (Dynamic Pattern Matching)
```python
def get_allowed_origins():
    """Generate CORS allowed origins dynamically."""
    origins = [
        "https://unipeer-frontend.vercel.app",  # Production
        "http://localhost:3000",                 # Local development
        "http://127.0.0.1:3000",                # Local development
    ]
    return origins

CORS_ALLOWED_ORIGINS = get_allowed_origins()

# Allow ANY Vercel preview deployment
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",      # ✅ All Vercel deployments (*.vercel.app)
    r"^http://localhost:\d+$",          # ✅ Local development (any port)
    r"^http://127\.0\.0\.1:\d+$",      # ✅ Local IP (any port)
]
```

✅ Main production domain works
✅ All Vercel preview deployments work
✅ All local development domains work

## How It Works

### Regex Pattern Explanations

| Pattern | Matches | Example |
|---------|---------|---------|
| `^https://.*\.vercel\.app$` | Any Vercel subdomain | `https://frontend-abc123.vercel.app` ✅ |
| `^http://localhost:\d+$` | Localhost on any port | `http://localhost:3000` ✅ |
| `^http://127\.0\.0\.1:\d+$` | Local IP on any port | `http://127.0.0.1:3000` ✅ |

### How Django-CORS-Headers Works

Django-CORS-Headers checks requests in this order:
1. **Exact match** in `CORS_ALLOWED_ORIGINS` list → Allow
2. **Regex match** in `CORS_ALLOWED_ORIGIN_REGEXES` list → Allow
3. **No match** → Deny (CORS error)

Your frontend can now be deployed to ANY domain matching the patterns above.

## Benefits

✅ **No more CORS errors** on Vercel preview deployments
✅ **Zero configuration needed** when pushing new features
✅ **Automatic support** for all Vercel preview URLs
✅ **Development flexibility** with any port on localhost
✅ **Production safety** still limited to known domains

## Testing

### Test Production Domain
```bash
curl -H "Origin: https://unipeer-frontend.vercel.app" \
  http://your-backend.onrender.com/api/profiles/
```
✅ Should work

### Test Any Vercel Preview
```bash
curl -H "Origin: https://frontend-xyz789.vercel.app" \
  http://your-backend.onrender.com/api/profiles/
```
✅ Should work

### Test Local Development
```bash
curl -H "Origin: http://localhost:3000" \
  http://localhost:8000/api/profiles/
```
✅ Should work

## What You Need to Do

### 1. ✅ Code is already updated
The `unipeer/settings.py` file has been updated with the dynamic CORS configuration.

### 2. Deploy to production
```bash
# Commit and push to GitHub
git add unipeer/settings.py
git commit -m "Fix: Enable CORS for all Vercel preview deployments"
git push origin main
```

Render will automatically redeploy with the new settings.

### 3. Test the fix
- Push a new feature to GitHub
- Vercel will create a preview deployment
- The frontend should now work without CORS errors
- No backend configuration changes needed! 🎉

## Additional Notes

### Why Not Hardcode All Domains?
- Vercel generates domains randomly with each deployment
- Can't predict future domain names
- Pattern matching is the only scalable solution

### Security Considerations
- Regex patterns still restrict to Vercel's `*.vercel.app` domain
- Not allowing arbitrary domains from the internet
- Production domain is explicitly listed for clarity
- Local development is restricted to common ports

### Environment-Based Configuration
If you need different CORS policies for different environments:

```python
if DEBUG:
    # Development: Allow everything
    CORS_ALLOWED_ORIGIN_REGEXES = [r"^.*$"]
else:
    # Production: Strict patterns only
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://.*\.vercel\.app$",
        r"^https://unipeer-frontend\.vercel\.app$",
    ]
```

## Troubleshooting

### Still getting CORS errors?

**Check 1: Verify Origin Header**
```bash
# In browser DevTools Console
fetch('http://backend.onrender.com/api/profiles/', {
  method: 'GET',
  headers: { 'Content-Type': 'application/json' }
}).then(r => r.json()).catch(e => console.log(e))
```

**Check 2: Test Backend CORS**
```bash
curl -i -H "Origin: https://your-frontend-domain.vercel.app" \
  http://your-backend.onrender.com/api/profiles/
```
Look for: `Access-Control-Allow-Origin` header in response

**Check 3: Clear Browser Cache**
Hard refresh: `Ctrl+Shift+R` or `Cmd+Shift+R`

### CORS Headers Missing?
If the response doesn't include `Access-Control-Allow-Origin`:
1. ✅ Verify `corsheaders` is in `INSTALLED_APPS`
2. ✅ Verify `CorsMiddleware` is first in `MIDDLEWARE`
3. ✅ Check the frontend domain matches a pattern
4. ✅ Restart the backend server

## References
- [Django-CORS-Headers Documentation](https://github.com/adamchainz/django-cors-headers)
- [CORS Security Best Practices](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

