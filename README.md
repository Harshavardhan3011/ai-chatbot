# 🥗 MacroSnap — Your AI Nutrition Buddy

**Snap it. Track it. Text yourself the results.**

MacroSnap is a Streamlit web app that uses Google Gemini to estimate calories and macronutrients from meal photos or text descriptions, and can send a full nutrition summary to your WhatsApp via Twilio.

![Python](https://img.shields.io/badge/python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/streamlit-latest-ff4b4b)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.0%20Flash-4285F4)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📸 Meal Photo Analysis | Upload a photo and get instant calorie & macro estimates |
| 💬 Text Meal Logging | Describe what you ate in plain text |
| 🧠 Conversation Memory | Follow-up questions understand context |
| 📤 WhatsApp Summary | Send your full nutrition report to your phone |
| 🎨 Polished UI | Clean, nutrition-themed interface |

---

## 🛠 Tech Stack

- **Frontend:** Streamlit
- **AI Engine:** Google Gemini 2.0 Flash (text + vision)
- **Messaging:** Twilio WhatsApp API
- **Language:** Python 3.9+

---

## 📁 Project Structure

```
macrosnap/
├── app.py                          # Main Streamlit application
├── prompts.py                      # AI system prompts & templates
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
└── .streamlit/
    ├── secrets.toml                # Your real secrets (NEVER commit)
    └── secrets.toml.example        # Template for secrets
```

---

## 🔑 Setup Guide

### 1. Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API Key** → **Create API key**.
3. Copy the key — you'll add it to `secrets.toml`.

### 2. Twilio WhatsApp Setup

#### a) Create a Twilio Account

1. Sign up at [twilio.com](https://www.twilio.com/).
2. Note your **Account SID** and **Auth Token** from the dashboard.

#### b) Activate the WhatsApp Sandbox

1. Go to **Messaging** → **Try it out** → **Send a WhatsApp message**.
2. Follow the instructions to join the sandbox (send a code from your WhatsApp to the Twilio number).
3. The sandbox number is typically `+14155238886`.

#### c) Create a Content Template

1. Go to **Messaging** → **Content Editor** in the Twilio console.
2. Create a new template with two variables:
   - `{{1}}` — User's name
   - `{{2}}` — Nutrition summary
3. Example template body:
   ```
   Hi {{1}}! 🥗 Here's your MacroSnap summary:

   {{2}}
   ```
4. Submit the template and copy the **Content SID** (starts with `HX`).

---

## 💻 Local Installation

### Prerequisites

- Python 3.9 or later
- pip

### Steps

```bash
# Clone the repository
git clone https://github.com/your-username/macrosnap.git
cd macrosnap

# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your secrets file
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# (or `cp` on macOS/Linux)
```

### Configure Secrets

Edit `.streamlit/secrets.toml` and fill in your real credentials:

```toml
GEMINI_API_KEY       = "AIza..."

TWILIO_ACCOUNT_SID   = "AC..."
TWILIO_AUTH_TOKEN     = "your-auth-token"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_CONTENT_SID   = "HX..."
```

### Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## ☁️ Streamlit Community Cloud Deployment

1. **Push to GitHub** (make sure `secrets.toml` is in `.gitignore`).
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Click **New app** → select your repo → set `app.py` as the entry point.
4. Open **Advanced settings** → **Secrets** and paste the contents of your `secrets.toml`.
5. Click **Deploy**.

### Post-Deployment Checklist

- [ ] Onboarding screen loads
- [ ] Text meal analysis works
- [ ] Image meal analysis works
- [ ] Conversation memory works (follow-up questions)
- [ ] WhatsApp summary sends successfully

---

## 🔒 Security Notes

- `secrets.toml` is in `.gitignore` and must **never** be committed.
- API keys are loaded from Streamlit Secrets, not hard-coded.
- WhatsApp numbers are validated before sending.
- Only JPG/JPEG/PNG images are accepted.
- Twilio auth tokens are never displayed in the UI.

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| "Gemini API key not found" | Add your key to `.streamlit/secrets.toml` |
| Rate limit errors | Wait a moment and try again |
| WhatsApp not received | Make sure you've joined the Twilio sandbox |
| Image upload fails | Only JPG, JPEG, and PNG are supported |
| "Send to WhatsApp" button is greyed out | Discuss at least one meal first, and ensure Twilio secrets are configured |
| Twilio error on send | Verify your Account SID, Auth Token, and Content SID |

---

## 📄 License

This project is for educational and personal use.

---

<p align="center">
  Built with ❤️ using Streamlit, Google Gemini & Twilio
</p>
