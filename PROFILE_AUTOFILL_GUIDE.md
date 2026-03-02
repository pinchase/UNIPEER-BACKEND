# 🔐 User Profile & Autofill - Complete Guide

## What Was Added

Added endpoints and improved responses to support **profile autofilling** on the frontend.

---

## 🎯 New Endpoints

### 1. Get Current User Profile: `/api/profiles/me/`

**Purpose:** Get the logged-in user's profile data without knowing their profile ID

**Method:** `GET`

**Authentication:** Required (JWT Bearer token)

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://unipeer-backend.onrender.com/api/profiles/me/
```

**Response:**
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
  "full_name": "John Doe",
  "display_name": "John Doe",
  "name": "John Doe",
  "bio": "Computer Science student...",
  "avatar_url": null,
  "university": "University of Nairobi",
  "department": "Computer Science",
  "year_of_study": 3,
  "gpa": 3.75,
  "interests": "AI, Machine Learning",
  "learning_goals": "Master full-stack development",
  "collaboration_preference": "project",
  "skills": [
    {"id": 1, "name": "Python", "category": "programming"},
    {"id": 2, "name": "Django", "category": "framework"}
  ],
  "courses": [
    {"id": 1, "code": "CS101", "name": "Intro to Programming", ...}
  ],
  "available_hours_per_week": 15,
  "preferred_time": "evening",
  "total_xp": 1250,
  "current_level": 5,
  "badges": [...],
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-03-01T14:20:00Z"
}
```

---

## 🔄 Updated Endpoints

### 2. Login: `/api/login/` (UPDATED)

**Purpose:** Authenticate user and get JWT tokens + profile data

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (UPDATED - Now includes JWT tokens):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
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
    "bio": "Computer Science student...",
    "university": "University of Nairobi",
    "department": "Computer Science",
    "year_of_study": 3,
    "skills": [...],
    "courses": [...],
    ...all profile fields...
  }
}
```

**What Changed:**
- ✅ Now returns JWT `access` and `refresh` tokens
- ✅ Returns complete user profile data in `user` field
- ✅ Frontend can store tokens and profile data immediately

---

### 3. Register: `/api/register/` (UPDATED)

**Purpose:** Create new user account and profile, get JWT tokens

**Method:** `POST`

**Authentication:** Not required (public endpoint)

**Request:**
```json
{
  "username": "janedoe",
  "email": "jane@example.com",
  "password": "securepass123",
  "first_name": "Jane",
  "last_name": "Doe",
  "bio": "Engineering student",
  "university": "University of Nairobi",
  "department": "Engineering",
  "year_of_study": 2,
  "interests": "Robotics, IoT",
  "learning_goals": "Build autonomous systems",
  "collaboration_preference": "project",
  "available_hours_per_week": 10,
  "preferred_time": "afternoon",
  "skill_ids": [1, 2, 3],
  "course_ids": [1, 2]
}
```

**Response (UPDATED - Now includes JWT tokens):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 2,
    "user": {
      "id": 2,
      "username": "janedoe",
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "jane@example.com"
    },
    ...all profile fields...
  }
}
```

**What Changed:**
- ✅ Now returns JWT `access` and `refresh` tokens
- ✅ Returns complete user profile data in `user` field
- ✅ User is automatically "logged in" after registration

---

## 🎨 Frontend Implementation Guide

### Step 1: Login Flow

```javascript
// Login function
async function login(email, password) {
  const response = await fetch('https://unipeer-backend.onrender.com/api/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  if (response.ok) {
    const data = await response.json();
    
    // Store tokens
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    
    // Store user data for autofill
    localStorage.setItem('user_data', JSON.stringify(data.user));
    localStorage.setItem('user_id', data.user.id);
    localStorage.setItem('profile_id', data.user.id);
    
    return data;
  }
  
  throw new Error('Login failed');
}
```

### Step 2: Get Current User Profile (for Autofill)

```javascript
// Get current user's profile
async function getMyProfile() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('https://unipeer-backend.onrender.com/api/profiles/me/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    const profile = await response.json();
    
    // Update stored user data
    localStorage.setItem('user_data', JSON.stringify(profile));
    
    return profile;
  }
  
  throw new Error('Failed to fetch profile');
}
```

### Step 3: Autofill Form Fields

```javascript
// Autofill profile edit form
function autofillProfileForm() {
  const userData = JSON.parse(localStorage.getItem('user_data'));
  
  if (!userData) {
    console.warn('No user data found');
    return;
  }
  
  // Fill basic info
  document.getElementById('first_name').value = userData.user.first_name || '';
  document.getElementById('last_name').value = userData.user.last_name || '';
  document.getElementById('email').value = userData.user.email || '';
  document.getElementById('username').value = userData.user.username || '';
  
  // Fill profile info
  document.getElementById('bio').value = userData.bio || '';
  document.getElementById('university').value = userData.university || '';
  document.getElementById('department').value = userData.department || '';
  document.getElementById('year_of_study').value = userData.year_of_study || '';
  document.getElementById('gpa').value = userData.gpa || '';
  document.getElementById('interests').value = userData.interests || '';
  document.getElementById('learning_goals').value = userData.learning_goals || '';
  document.getElementById('collaboration_preference').value = userData.collaboration_preference || '';
  document.getElementById('available_hours_per_week').value = userData.available_hours_per_week || '';
  document.getElementById('preferred_time').value = userData.preferred_time || '';
  
  // Fill skills (if you have a multi-select)
  if (userData.skills && userData.skills.length > 0) {
    const skillIds = userData.skills.map(s => s.id);
    // Set selected skills in your UI
    selectSkills(skillIds);
  }
  
  // Fill courses
  if (userData.courses && userData.courses.length > 0) {
    const courseIds = userData.courses.map(c => c.id);
    selectCourses(courseIds);
  }
}

// Call this when profile page loads
document.addEventListener('DOMContentLoaded', () => {
  // If user is logged in, autofill the form
  if (localStorage.getItem('access_token')) {
    autofillProfileForm();
  }
});
```

### Step 4: Update Profile

```javascript
// Update user profile
async function updateProfile(profileData) {
  const token = localStorage.getItem('access_token');
  const userData = JSON.parse(localStorage.getItem('user_data'));
  const profileId = userData.id;
  
  const response = await fetch(
    `https://unipeer-backend.onrender.com/api/profiles/${profileId}/`,
    {
      method: 'PATCH', // or 'PUT' for full update
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    }
  );
  
  if (response.ok) {
    const updatedProfile = await response.json();
    
    // Update stored user data
    localStorage.setItem('user_data', JSON.stringify(updatedProfile));
    
    return updatedProfile;
  }
  
  throw new Error('Failed to update profile');
}

// Example usage
async function handleProfileUpdate(event) {
  event.preventDefault();
  
  const formData = {
    bio: document.getElementById('bio').value,
    university: document.getElementById('university').value,
    department: document.getElementById('department').value,
    year_of_study: parseInt(document.getElementById('year_of_study').value),
    interests: document.getElementById('interests').value,
    learning_goals: document.getElementById('learning_goals').value,
    skill_ids: getSelectedSkillIds(), // Your function to get selected skills
    course_ids: getSelectedCourseIds() // Your function to get selected courses
  };
  
  try {
    await updateProfile(formData);
    alert('Profile updated successfully!');
  } catch (error) {
    alert('Failed to update profile: ' + error.message);
  }
}
```

### Step 5: Registration Flow (Auto-login after signup)

```javascript
// Register and auto-login
async function register(formData) {
  const response = await fetch('https://unipeer-backend.onrender.com/api/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(formData)
  });
  
  if (response.ok) {
    const data = await response.json();
    
    // Store tokens (user is now logged in!)
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    
    // Store user data
    localStorage.setItem('user_data', JSON.stringify(data.user));
    localStorage.setItem('user_id', data.user.id);
    
    // Redirect to dashboard or profile
    window.location.href = '/dashboard.html';
    
    return data;
  }
  
  throw new Error('Registration failed');
}
```

---

## 📊 Data Flow Summary

### Login/Register Flow:
```
User submits credentials
    ↓
Backend authenticates
    ↓
Backend generates JWT tokens
    ↓
Backend fetches user profile
    ↓
Returns: { access, refresh, user: {...all profile data...} }
    ↓
Frontend stores tokens + user data
    ↓
Frontend can now:
  - Make authenticated requests
  - Autofill forms with user data
  - Display user info
```

### Profile Page Load:
```
Page loads
    ↓
Check if user logged in (has access_token)
    ↓
Get user data from localStorage
    ↓
Autofill form fields with stored data
    ↓
User can edit and save changes
    ↓
Updated data stored back to localStorage
```

### Refresh Profile Data:
```
Call /api/profiles/me/ with JWT token
    ↓
Get latest profile data from server
    ↓
Update localStorage
    ↓
Update UI with fresh data
```

---

## 🎯 Key Benefits

### For Frontend:
1. ✅ **Automatic Login After Registration** - Users don't need to login separately
2. ✅ **Profile Data Available Immediately** - No extra API call needed after login
3. ✅ **Easy Form Autofill** - All user data in one object
4. ✅ **Simple Profile Updates** - Just PATCH to `/api/profiles/{id}/`
5. ✅ **Current User Endpoint** - `/api/profiles/me/` works without knowing profile ID

### For Backend:
1. ✅ **Consistent Response Format** - Login and Register return same structure
2. ✅ **JWT Token Generation** - Built-in with `rest_framework_simplejwt`
3. ✅ **Complete Profile Data** - Includes user, skills, courses, badges
4. ✅ **Proper Authentication** - `/api/profiles/me/` requires valid JWT token

---

## 🔒 Security Notes

### Data Returned in Login/Register:
- ✅ **Access Token** - Short-lived (1 hour default)
- ✅ **Refresh Token** - Longer-lived (7 days default)
- ✅ **User Profile** - Complete profile data (safe to return, user's own data)

### What's NOT Returned:
- ❌ **Password** - Never returned (write-only field)
- ❌ **Other Users' Private Data** - Only own profile
- ❌ **Sensitive System Data** - Only user-facing data

### Endpoints Security:
- 🔓 `/api/login/` - Public (AllowAny)
- 🔓 `/api/register/` - Public (AllowAny)
- 🔒 `/api/profiles/me/` - Protected (IsAuthenticated)
- 🔒 `/api/profiles/{id}/` - Protected (IsAuthenticated + permissions)

---

## 📝 API Endpoints Summary

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/register/` | POST | No | Create account + get tokens |
| `/api/login/` | POST | No | Login + get tokens |
| `/api/profiles/me/` | GET | Yes | Get current user's profile |
| `/api/profiles/{id}/` | GET | Yes | Get specific profile |
| `/api/profiles/{id}/` | PATCH | Yes | Update profile |
| `/api/profiles/{id}/dashboard/` | GET | Yes | Get dashboard data |

---

## 🚀 Testing

### Test 1: Register and Auto-Login
```bash
curl -X POST https://unipeer-backend.onrender.com/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@test.com",
    "password": "test123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Should return:
# {
#   "access": "eyJ0...",
#   "refresh": "eyJ0...",
#   "user": {...}
# }
```

### Test 2: Login and Get Profile
```bash
curl -X POST https://unipeer-backend.onrender.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "test123"
  }'

# Should return:
# {
#   "access": "eyJ0...",
#   "refresh": "eyJ0...",
#   "user": {...}
# }
```

### Test 3: Get Current User Profile
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://unipeer-backend.onrender.com/api/profiles/me/

# Should return complete profile data
```

---

## ✅ What's Fixed

| Issue | Before | After |
|-------|--------|-------|
| Login response | ❌ Only profile data, no tokens | ✅ Tokens + profile data |
| Register response | ❌ Only profile data, no tokens | ✅ Tokens + profile data |
| Get current user | ❌ No endpoint | ✅ `/api/profiles/me/` |
| Form autofill | ❌ Complex, needs profile ID | ✅ Simple, use stored data |
| Auto-login after register | ❌ Not possible | ✅ Tokens returned |

---

## 🎉 Summary

**What Was Added:**
- ✅ `/api/profiles/me/` endpoint to get current user's profile
- ✅ JWT tokens in login response
- ✅ JWT tokens in register response
- ✅ Complete profile data in both responses

**How Frontend Uses It:**
1. User logs in/registers → Get tokens + profile data
2. Store tokens + profile data in localStorage
3. Use tokens for authenticated requests
4. Use profile data to autofill forms
5. Call `/api/profiles/me/` to refresh profile data
6. Update profile via PATCH to `/api/profiles/{id}/`

**Result:**
- ✅ Forms can be autofilled easily
- ✅ User data always available
- ✅ Seamless login/registration experience
- ✅ Proper JWT authentication

---

**Status:** ✅ READY TO USE

**Deploy and test the new endpoints!** 🚀

