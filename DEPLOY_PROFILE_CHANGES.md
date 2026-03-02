# 🚀 DEPLOY CHECKLIST - Profile Autofill Changes

## Changes Summary

✅ **Added `/api/profiles/me/` endpoint** - Get current user's profile
✅ **Updated `/api/login/`** - Returns JWT tokens + complete profile data
✅ **Updated `/api/register/`** - Returns JWT tokens + complete profile data

---

## Files Modified

- ✅ `api/views.py` - Added `me()` action, updated LoginView and RegisterView

---

## Deploy Steps

### 1. Commit Changes
```bash
cd "/home/pinchase/Desktop/Untitled Folder 2/frontend-sample/backend"

git add api/views.py
git commit -m "feat: Add profile autofill support

- Add /api/profiles/me/ endpoint for current user
- Update login to return JWT tokens + profile data
- Update register to return JWT tokens + profile data
- Enable auto-login after registration
- Support form autofilling with user data"

git push origin main
```

### 2. Wait for Render Deploy
Render will auto-deploy (5-10 minutes)

### 3. Test New Endpoints

**Test 1: Register and get tokens**
```bash
curl -X POST https://unipeer-backend.onrender.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test2@test.com",
    "password": "test123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Should return:
# {
#   "access": "eyJ0...",
#   "refresh": "eyJ0...",
#   "user": {...complete profile...}
# }
```

**Test 2: Login and get tokens**
```bash
curl -X POST https://unipeer-backend.onrender.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test2@test.com",
    "password": "test123"
  }'

# Should return:
# {
#   "access": "eyJ0...",
#   "refresh": "eyJ0...",
#   "user": {...complete profile...}
# }
```

**Test 3: Get current user profile**
```bash
# Use access token from above
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://unipeer-backend.onrender.com/api/profiles/me/

# Should return complete profile data
```

---

## Frontend Changes Needed

### 1. Update Login Handler
```javascript
// OLD
const profile = await login(email, password);
// profile was just profile data

// NEW
const response = await login(email, password);
const { access, refresh, user } = response;
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);
localStorage.setItem('user_data', JSON.stringify(user));
```

### 2. Update Register Handler
```javascript
// NEW - Same as login
const response = await register(formData);
const { access, refresh, user } = response;
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);
localStorage.setItem('user_data', JSON.stringify(user));
// User is now logged in!
```

### 3. Add Autofill Function
```javascript
function autofillProfileForm() {
  const userData = JSON.parse(localStorage.getItem('user_data'));
  if (!userData) return;
  
  document.getElementById('first_name').value = userData.user.first_name || '';
  document.getElementById('last_name').value = userData.user.last_name || '';
  document.getElementById('email').value = userData.user.email || '';
  document.getElementById('bio').value = userData.bio || '';
  document.getElementById('university').value = userData.university || '';
  document.getElementById('department').value = userData.department || '';
  document.getElementById('year_of_study').value = userData.year_of_study || '';
  document.getElementById('interests').value = userData.interests || '';
  document.getElementById('learning_goals').value = userData.learning_goals || '';
  // ... etc
}

// Call on page load
window.addEventListener('DOMContentLoaded', autofillProfileForm);
```

### 4. Add Profile Refresh Function
```javascript
async function refreshProfile() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/profiles/me/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const profile = await response.json();
  localStorage.setItem('user_data', JSON.stringify(profile));
  return profile;
}
```

---

## Expected Behavior

### After Login:
1. ✅ User gets JWT tokens
2. ✅ User gets complete profile data
3. ✅ Frontend stores both
4. ✅ User can navigate to profile page
5. ✅ Profile form is autofilled

### After Registration:
1. ✅ User gets JWT tokens immediately
2. ✅ User gets complete profile data
3. ✅ Frontend stores both
4. ✅ User is logged in (no separate login needed)
5. ✅ User redirected to dashboard/profile

### On Profile Page:
1. ✅ Form loads with user's data pre-filled
2. ✅ User can edit fields
3. ✅ User can save changes
4. ✅ Updated data stored back to localStorage

---

## Verification Checklist

After deployment:

- [ ] `/api/register/` returns tokens + user data
- [ ] `/api/login/` returns tokens + user data
- [ ] `/api/profiles/me/` returns current user's profile
- [ ] Frontend can autofill profile form
- [ ] Frontend can update profile
- [ ] Auto-login after registration works
- [ ] No CORS errors
- [ ] No authentication errors

---

## API Response Examples

### Login/Register Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "user": {
      "id": 1,
      "username": "johndoe",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com"
    },
    "full_name": "John Doe",
    "display_name": "John Doe",
    "name": "John Doe",
    "bio": "Computer Science student passionate about AI",
    "avatar_url": null,
    "university": "University of Nairobi",
    "department": "Computer Science",
    "year_of_study": 3,
    "gpa": 3.75,
    "interests": "AI, Machine Learning, Web Development",
    "learning_goals": "Master full-stack development",
    "collaboration_preference": "project",
    "skills": [
      {"id": 1, "name": "Python", "category": "programming", "description": ""},
      {"id": 2, "name": "Django", "category": "framework", "description": ""}
    ],
    "courses": [
      {"id": 1, "code": "CS101", "name": "Intro to CS", "department": "CS", "level": 100}
    ],
    "available_hours_per_week": 15,
    "preferred_time": "evening",
    "total_xp": 1250,
    "current_level": 5,
    "badges": [],
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-03-01T14:20:00Z"
  }
}
```

### /api/profiles/me/ Response:
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  ...same as user object above...
}
```

---

## Documentation

- **Complete Guide:** `PROFILE_AUTOFILL_GUIDE.md`
- **Quick Summary:** `Profile Autofill Complete.md` (this file)

---

## Status

✅ **Backend Changes:** COMPLETE
⏳ **Deployment:** Ready to deploy
⏳ **Frontend Changes:** Needed (see above)
⏳ **Testing:** After deployment

---

**Everything is ready to deploy!** 🚀

Push the changes and test the new endpoints.

