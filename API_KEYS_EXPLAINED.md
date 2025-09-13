# 🔑 API Keys Explanation - TalkingPhoto AI MVP

## Your Active API Keys & What They Do

### 1. 🤖 GEMINI_API_KEY

**Key:** `AIzaSyBVvo-cEZzLwJfiHR6pC5dFOVLxZaryGKU`  
**Provider:** Google AI Studio (FREE)  
**What it does:**

- **Script Generation**: Creates engaging, personalized scripts from user prompts
- **Photo Analysis**: Detects faces, expressions, and image quality
- **Content Enhancement**: Improves photo quality and composition
- **Basic Lip Sync**: Generates mouth movement patterns
- **Smart Cropping**: Automatically centers on faces

**Features Enabled:**

- ✅ AI-powered script writing
- ✅ Face detection and analysis
- ✅ Expression recognition
- ✅ Photo enhancement
- ✅ Basic lip synchronization

**Cost:** FREE (60 requests/minute limit)

---

### 2. 🎙️ GOOGLE_AI_API_KEY

**Key:** `AIzaSyBCQtNVqS3ZnyF09yzKc547dFyJ_4hOp-A`  
**Provider:** Google Cloud Platform  
**What it does:**

- **Text-to-Speech**: Converts scripts into natural-sounding voices
- **Voice Options**: Multiple voices, languages, and accents
- **Audio Quality**: High-quality MP3 generation
- **Speed Control**: Adjust speaking rate and pitch

**Features Enabled:**

- ✅ Natural voice generation
- ✅ 100+ language support
- ✅ Multiple voice personalities
- ✅ Audio customization
- ✅ Download as MP3

**Cost:** FREE (1 million characters/month)

---

### 3. ☁️ CLOUDINARY (Storage)

**Cloud Name:** `da3qhmqa5`  
**API Key:** `854916998285751`  
**What it does:**

- **File Storage**: Stores user photos and generated content
- **CDN Delivery**: Fast global content delivery
- **Image Optimization**: Automatic format conversion and compression
- **Secure URLs**: Protected file access

**Features Enabled:**

- ✅ 25GB free storage
- ✅ Automatic backups
- ✅ Fast loading worldwide
- ✅ Image transformations
- ✅ Video storage ready

**Cost:** FREE (25GB storage, 25GB bandwidth/month)

---

### 4. 🗄️ SUPABASE (Database)

**Database URL:** PostgreSQL on Supabase  
**What it does:**

- **User Management**: Registration, login, profiles
- **Session Tracking**: Secure authentication
- **Usage History**: Track generations and limits
- **File Management**: Link files to users

**Features Enabled:**

- ✅ User authentication
- ✅ JWT token security
- ✅ Usage analytics
- ✅ File history
- ✅ Subscription management ready

**Cost:** FREE (500MB database, 2GB bandwidth)

---

## 🚀 How They Work Together

```mermaid
graph LR
    A[User Upload] --> B[Cloudinary Storage]
    B --> C[Gemini Vision API]
    C --> D[Face Detection & Enhancement]
    D --> E[Gemini AI Script]
    E --> F[Google TTS Voice]
    F --> G[Basic Lip Sync]
    G --> H[Export Package]
    H --> I[User Download]
```

### Complete Workflow:

1. **Photo Upload** → Cloudinary stores the image securely
2. **AI Analysis** → Gemini Vision detects face and quality
3. **Enhancement** → AI improves photo (brightness, sharpness)
4. **Script Creation** → Gemini AI writes personalized script
5. **Voice Generation** → Google TTS creates natural voice
6. **Lip Sync** → Basic mouth movement generation
7. **Export Package** → Bundle with instructions for D-ID/HeyGen

---

## 💰 Cost Breakdown (Per User)

| Feature          | API Used   | Free Tier   | Cost After Free  |
| ---------------- | ---------- | ----------- | ---------------- |
| Photo Storage    | Cloudinary | 25GB total  | $89/month        |
| AI Processing    | Gemini     | 60 req/min  | $0.00015/request |
| Voice Generation | Google TTS | 1M chars/mo | $4/million chars |
| Database         | Supabase   | 500MB       | $25/month        |

**Estimated Cost per Video:**

- Free tier: **₹0** (completely free)
- After limits: **₹0.50** per video

**Break-even Analysis:**

- Free tier supports: ~1000 videos/month
- At ₹999/month subscription: Need only 2 customers
- Target ₹1 Cr MRR: Need 1,001 customers

---

## 🔒 Security Notes

**DO NOT:**

- ❌ Share these keys publicly
- ❌ Commit to GitHub
- ❌ Post in forums

**DO:**

- ✅ Use Streamlit Secrets
- ✅ Keep backups secure
- ✅ Rotate keys periodically
- ✅ Monitor usage

---

## 📊 API Limits & Monitoring

### Daily Limits:

- **Gemini**: 1,500 requests/day free
- **Google TTS**: 33,000 characters/day free
- **Cloudinary**: Unlimited requests
- **Supabase**: Unlimited queries

### Monitoring:

- Google Cloud Console: https://console.cloud.google.com
- Cloudinary Dashboard: https://cloudinary.com/console
- Supabase Dashboard: https://app.supabase.com

---

## 🎯 Next Steps

1. ✅ APIs configured and tested
2. ✅ Features enabled in app
3. ⏳ Deploy to Streamlit Cloud
4. ⏳ Add payment integration
5. ⏳ Launch marketing campaign

---

## 🆘 Troubleshooting

**If Gemini fails:**

- Check API key in .env
- Verify model name: `gemini-1.5-flash`
- Check rate limits

**If TTS fails:**

- Ensure Google Cloud project active
- Check Text-to-Speech API enabled
- Verify billing account (free tier OK)

**If Cloudinary fails:**

- Check all 3 credentials
- Verify upload preset
- Check storage limits

**If Database fails:**

- Check Supabase project status
- Verify connection string
- Check if tables migrated

---

**Your app is ready to generate AI talking photos! 🎉**
