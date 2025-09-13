# 🤖 Automated Setup Instructions for TalkingPhoto AI MVP

## Complete Step-by-Step Browser Automation Commands

### ✅ Already Completed:

1. GitHub repository: https://github.com/srijanarya/alkingphoto-ai-mvp
2. Streamlit app deployed: https://alkingphoto-ai-mvp-fnyuyh3wm6ofnev3fbseeo.streamlit.app/
3. Google Cloud project created: talkingphoto-ai

---

## 📋 TASK 1: Get Google Cloud API Key

### Steps for Browser Automation:

1. **Navigate to:** `https://console.cloud.google.com/apis/credentials`
2. **Wait for page load** (2 seconds)
3. **Click button with text:** "CREATE CREDENTIALS"
4. **From dropdown menu, click:** "API key"
5. **Wait for modal** (2 seconds)
6. **Copy the text that starts with:** `AIza`
7. **Save to clipboard as:** GOOGLE_API_KEY
8. **Click button:** "RESTRICT KEY"
9. **In the form, find section:** "API restrictions"
10. **Click radio button:** "Restrict key"
11. **Check these checkboxes:**
    - Cloud Storage API
    - Generative Language API
    - Vertex AI API
12. **Click button:** "SAVE"
13. **Store the API key in a file:** `credentials.txt`

---

## 📋 TASK 2: Get Google AI Studio (Gemini) API Key - FREE

### Steps for Browser Automation:

1. **Navigate to:** `https://aistudio.google.com/app/apikey`
2. **Wait for page load** (2 seconds)
3. **Click button with text:** "Create API key"
4. **If dropdown appears, select:** "Create API key in new project"
5. **Wait for key generation** (3 seconds)
6. **Copy the text that starts with:** `AIza`
7. **Save to clipboard as:** GEMINI_API_KEY
8. **Store in file:** `credentials.txt`

---

## 📋 TASK 3: Create Supabase Database (FREE)

### Steps for Browser Automation:

1. **Navigate to:** `https://supabase.com`
2. **Click button:** "Start your project"
3. **Click button:** "Sign in with GitHub"
4. **Authorize if needed**
5. **Once logged in, click:** "New project"
6. **Fill form fields:**
   - Name field: `talkingphoto-db`
   - Database Password field: `TalkingPhoto2024!Secure`
   - Region dropdown: Select `South Asia (Mumbai)`
7. **Click button:** "Create new project"
8. **Wait for provisioning** (120 seconds)
9. **Navigate to:** Settings → Database
10. **Copy and save these values:**
    - Connection string (starts with `postgresql://`)
    - Save as: DATABASE_URL
11. **Navigate to:** SQL Editor
12. **Paste this SQL and execute:**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    input_image_url TEXT,
    output_video_url TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    stripe_payment_id VARCHAR(255),
    amount INTEGER,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

13. **Click button:** "Run"

---

## 📋 TASK 4: Create Cloudinary Account (FREE Storage)

### Steps for Browser Automation:

1. **Navigate to:** `https://cloudinary.com/users/register_free`
2. **Fill form fields:**
   - Full Name: `Your Name`
   - Email: `your-email@gmail.com`
   - Password: `SecurePassword2024!`
   - Company: `TalkingPhoto AI`
3. **Click button:** "Create Account"
4. **Verify email** (check inbox)
5. **After verification, navigate to:** Dashboard
6. **Copy and save these values:**
   - Cloud Name: (shown on dashboard)
   - API Key: (shown on dashboard)
   - API Secret: (click "View" to reveal)
7. **Save all to:** `credentials.txt`

---

## 📋 TASK 5: Create Upstash Redis (FREE Cache)

### Steps for Browser Automation:

1. **Navigate to:** `https://upstash.com`
2. **Click button:** "Start for Free"
3. **Click button:** "Continue with GitHub"
4. **Authorize if needed**
5. **Click button:** "Create Database"
6. **Fill form fields:**
   - Name: `talkingphoto-cache`
   - Region dropdown: Select `aws-ap-south-1 (Mumbai)`
   - Enable TLS: Check this box
7. **Click button:** "Create"
8. **Copy and save from Details tab:**
   - Endpoint: (shown on page)
   - Password: (shown on page)
   - REST URL: (shown on page)
9. **Save to:** `credentials.txt`

---

## 📋 TASK 6: Create Stripe Account (For Payments)

### Steps for Browser Automation:

1. **Navigate to:** `https://dashboard.stripe.com/register`
2. **Fill form fields:**
   - Email: `your-email@gmail.com`
   - Full name: `Your Name`
   - Password: `SecureStripe2024!`
   - Country dropdown: `India`
3. **Click button:** "Create account"
4. **Verify email**
5. **Navigate to:** Developers → API keys
6. **Copy and save:**
   - Publishable key: (starts with `pk_test_`)
   - Secret key: (click "Reveal" then copy, starts with `sk_test_`)
7. **Save to:** `credentials.txt`

---

## 📋 TASK 7: Configure Streamlit App with Secrets

### Steps for Browser Automation:

1. **Navigate to:** `https://share.streamlit.io/`
2. **Click on your app:** `alkingphoto-ai-mvp`
3. **Click:** "Settings" (gear icon)
4. **Click:** "Secrets"
5. **Paste this configuration (replace with actual values from credentials.txt):**

```toml
# Google Cloud
GOOGLE_API_KEY = "AIza..."
GEMINI_API_KEY = "AIza..."

# Database
DATABASE_URL = "postgresql://postgres:[password]@[host]:5432/postgres"

# Redis Cache
REDIS_ENDPOINT = "..."
REDIS_PASSWORD = "..."
REDIS_REST_URL = "https://..."

# Cloudinary Storage
CLOUDINARY_CLOUD_NAME = "..."
CLOUDINARY_API_KEY = "..."
CLOUDINARY_API_SECRET = "..."

# Stripe Payments
STRIPE_PUBLISHABLE_KEY = "pk_test_..."
STRIPE_SECRET_KEY = "sk_test_..."

# App Config
APP_ENV = "production"
APP_SECRET_KEY = "your-secret-key-change-this"
```

6. **Click button:** "Save"
7. **App will automatically restart**

---

## 📋 FINAL OUTPUT FILE: credentials.txt

After automation, you should have a file with:

```
GOOGLE_API_KEY=AIza...
GEMINI_API_KEY=AIza...
DATABASE_URL=postgresql://...
REDIS_ENDPOINT=...
REDIS_PASSWORD=...
REDIS_REST_URL=https://...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

---

## 🎯 Success Criteria:

- All API keys collected in credentials.txt
- All services have free tier activated
- Streamlit app configured with secrets
- No credit card required except for Stripe (for receiving payments)

## 🤖 For Playwright/Selenium:

- Use explicit waits (2-3 seconds) after navigation
- Use text-based selectors when possible
- Save all credentials to a single file
- Take screenshots after each major step for verification
