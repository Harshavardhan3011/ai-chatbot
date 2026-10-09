"""
app.py — MacroSnap: Your AI Nutrition Buddy

A Streamlit application that uses Google Gemini for meal analysis
and Twilio for sending nutrition summaries to WhatsApp.
"""

import json
import re
import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from prompts import (
    SYSTEM_INSTRUCTION,
    DEFAULT_IMAGE_PROMPT,
    SUMMARY_PROMPT,
    welcome_message,
)

# ────────────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"]
MAX_WHATSAPP_CHARS = 1500

# ────────────────────────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MacroSnap — AI Nutrition Buddy",
    page_icon="🥗",
    layout="centered",
)

# ────────────────────────────────────────────────────────────────────
# Custom CSS — polished, nutrition-themed UI
# ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Import modern font ──────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ──────────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Main container ──────────────────────────────────────── */
    .main .block-container {
        max-width: 760px;
        padding-top: 1.5rem;
        padding-bottom: 6rem;
    }

    /* ── Header ──────────────────────────────────────────────── */
    .app-header {
        text-align: center;
        padding: 1rem 0 0.5rem;
    }
    .app-header h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2d8a4e, #56c47a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem;
        letter-spacing: -0.5px;
    }
    .app-header p {
        color: #6b7b8d;
        font-size: 1.05rem;
        font-weight: 500;
        margin: 0;
    }

    /* ── App Header Bar with Button Beside ───────────────────── */
    .app-title-block h1 {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2d8a4e, #56c47a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.1rem;
        letter-spacing: -0.5px;
    }
    .app-title-block p {
        color: #6b7b8d;
        font-size: 0.95rem;
        font-weight: 500;
        margin: 0;
    }

    /* ── Onboarding card ─────────────────────────────────────── */
    .onboarding-card {
        background: linear-gradient(145deg, #ffffff, #f0faf3);
        border: 1px solid #d4edda;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin: 1.5rem auto;
        max-width: 460px;
        box-shadow: 0 4px 24px rgba(45,138,78,0.08);
    }
    .onboarding-card h2 {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a3c2a;
        margin-bottom: 0.25rem;
    }
    .onboarding-card .subtitle {
        text-align: center;
        color: #6b8f7b;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* ── Chat messages ───────────────────────────────────────── */
    .stChatMessage {
        border-radius: 14px !important;
        margin-bottom: 0.5rem !important;
    }

    /* ── WhatsApp button styling ─────────────────────────────── */
    div[data-testid="stButton"] > button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }

    /* ── Success / error banners ─────────────────────────────── */
    .stAlert {
        border-radius: 12px !important;
    }

    /* ── Divider ─────────────────────────────────────────────── */
    .section-divider {
        border: none;
        border-top: 1px solid #e0ece4;
        margin: 0.85rem 0 1rem;
    }

    /* ── Subtle footer ───────────────────────────────────────── */
    .footer-note {
        text-align: center;
        color: #a0b0a8;
        font-size: 0.78rem;
        margin-top: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ────────────────────────────────────────────────────────────────────
# Helper: validate secrets are present
# ────────────────────────────────────────────────────────────────────
def _check_gemini_secrets() -> bool:
    """Return True if the Gemini API key is configured."""
    key = st.secrets.get("GEMINI_API_KEY", "")
    return bool(key and key != "your-gemini-api-key-here")


def _check_twilio_secrets() -> bool:
    """Return True if all four Twilio secrets are configured."""
    required = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_WHATSAPP_FROM",
        "TWILIO_CONTENT_SID",
    ]
    for key in required:
        val = st.secrets.get(key, "")
        if not val or "your-" in val:
            return False
    return True


# ────────────────────────────────────────────────────────────────────
# Gemini client — created once and cached
# ────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_gemini_client():
    """Initialise the Google GenAI client (cached across reruns)."""
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def create_chat_session():
    """
    Start a new Gemini chat session with the nutrition system prompt.
    This is stored in session_state (not cached) because each user
    needs their own conversation history.
    """
    client = get_gemini_client()
    chat = client.chats.create(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )
    return chat


# ────────────────────────────────────────────────────────────────────
# Twilio client — created once and cached
# ────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_twilio_client():
    """Initialise and cache the Twilio REST client."""
    return TwilioClient(
        st.secrets["TWILIO_ACCOUNT_SID"],
        st.secrets["TWILIO_AUTH_TOKEN"],
    )


# ────────────────────────────────────────────────────────────────────
# Message helpers
# ────────────────────────────────────────────────────────────────────
def add_message(role: str, content, kind: str = "text"):
    """Append a message dict to session_state.messages."""
    st.session_state.messages.append(
        {"role": role, "kind": kind, "content": content}
    )


def render_message(msg: dict):
    """Display a single message in the Streamlit chat UI."""
    with st.chat_message(msg["role"]):
        if msg["kind"] == "image":
            st.image(msg["content"], use_container_width=True)
        else:
            st.markdown(msg["content"])


def ask_gemini(parts: list) -> str:
    """
    Send a message (text and/or image parts) to the Gemini chat session.
    Returns the assistant's text response.
    """
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text
    except Exception as exc:
        error_msg = str(exc).lower()
        if "rate" in error_msg or "quota" in error_msg:
            return (
                "⚠️ I've hit a rate limit — please wait a moment "
                "and try again."
            )
        if "invalid" in error_msg and "key" in error_msg:
            return (
                "⚠️ The Gemini API key appears to be invalid. "
                "Please check your configuration."
            )
        return "⚠️ Something went wrong while analysing your request. Please try again."


# ────────────────────────────────────────────────────────────────────
# WhatsApp helpers
# ────────────────────────────────────────────────────────────────────
def clean_whatsapp_text(text: str) -> str:
    """
    Sanitise a summary for WhatsApp:
    - Collapse excessive whitespace
    - Remove markdown formatting
    - Trim to ~1 500 characters
    - Return fallback if empty
    """
    if not text or not text.strip():
        return "No nutrition summary available."

    # Remove markdown bold/italic markers
    text = re.sub(r"[*_]{1,2}", "", text)
    # Collapse multiple blank lines to one
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = text.strip()

    if len(text) > MAX_WHATSAPP_CHARS:
        text = text[: MAX_WHATSAPP_CHARS - 3].rstrip() + "..."

    return text


def send_whatsapp(to_number: str, user_name: str, summary: str):
    """
    Send a WhatsApp message via Twilio Content API.
    Returns (success: bool, detail: str).
    """
    try:
        client = get_twilio_client()

        recipient = to_number.strip()
        if not recipient.startswith("+"):
            recipient = "+" + recipient

        to_formatted = (
            recipient
            if recipient.startswith("whatsapp:")
            else f"whatsapp:{recipient}"
        )

        from_raw = st.secrets["TWILIO_WHATSAPP_FROM"].strip()
        from_formatted = (
            from_raw
            if from_raw.startswith("whatsapp:")
            else f"whatsapp:{from_raw}"
        )

        cleaned_summary = clean_whatsapp_text(summary)
        content_variables = json.dumps({
            "1": user_name,
            "2": cleaned_summary,
        })

        message = client.messages.create(
            from_=from_formatted,
            to=to_formatted,
            content_sid=st.secrets["TWILIO_CONTENT_SID"],
            content_variables=content_variables,
        )
        return True, message.sid
    except TwilioRestException as exc:
        return False, f"Twilio error: {exc.msg}"
    except Exception:
        return False, "Unable to send WhatsApp message. Check Twilio configuration and messaging status."


def validate_whatsapp_number(number: str) -> bool:
    """Basic validation: starts with + and has 10-15 digits after."""
    return bool(re.match(r"^\+\d{10,15}$", number))


# ────────────────────────────────────────────────────────────────────
# Initialise session state defaults
# ────────────────────────────────────────────────────────────────────
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "user_phone" not in st.session_state:
    st.session_state.user_phone = ""
if "meal_discussed" not in st.session_state:
    st.session_state.meal_discussed = False


# ────────────────────────────────────────────────────────────────────
# Gate: Gemini API key must be configured
# ────────────────────────────────────────────────────────────────────
if not _check_gemini_secrets():
    st.markdown(
        '<div class="app-header">'
        "<h1>🥗 MacroSnap</h1>"
        "<p>Your AI nutrition buddy</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.error(
        "**Gemini API key not found.**\n\n"
        "Add your key to `.streamlit/secrets.toml`:\n\n"
        '```\nGEMINI_API_KEY = "your-key-here"\n```'
    )
    st.stop()


# ════════════════════════════════════════════════════════════════════
#  ONBOARDING SCREEN
# ════════════════════════════════════════════════════════════════════
if not st.session_state.onboarded:
    st.markdown(
        '<div class="app-header">'
        "<h1>🥗 MacroSnap</h1>"
        "<p>Snap it. Track it. Text yourself the results.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="onboarding-card">', unsafe_allow_html=True)
    st.markdown(
        "<h2>Welcome!</h2>"
        '<p class="subtitle">Tell us a little about yourself to get started.</p>',
        unsafe_allow_html=True,
    )

    with st.form("onboarding_form"):
        name = st.text_input(
            "Your name",
            placeholder="e.g. Harsha",
        )
        phone = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
        )
        submitted = st.form_submit_button("Let's Go 🚀", use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        # ── Validate ────────────────────────────────────────────
        if not name.strip():
            st.warning("Please enter your name.")
            st.stop()
        if not phone.strip():
            st.warning("Please enter your WhatsApp number.")
            st.stop()
        if not validate_whatsapp_number(phone.strip()):
            st.warning(
                "Please enter a valid WhatsApp number "
                "starting with **+** and your country code "
                "(e.g. +91XXXXXXXXXX)."
            )
            st.stop()

        # ── Save user info ──────────────────────────────────────
        st.session_state.user_name = name.strip()
        st.session_state.user_phone = phone.strip()

        # ── Create Gemini chat session ──────────────────────────
        st.session_state.chat = create_chat_session()

        # ── Add the welcome message to history ──────────────────
        welcome = welcome_message(name.strip())
        add_message("assistant", welcome)

        st.session_state.onboarded = True
        st.rerun()

    st.markdown(
        '<p class="footer-note">Powered by Google Gemini & Twilio</p>',
        unsafe_allow_html=True,
    )
    st.stop()


# ════════════════════════════════════════════════════════════════════
#  MAIN APP (after onboarding)
# ════════════════════════════════════════════════════════════════════

# ── Header bar with title and WhatsApp action button beside it ───────
header_col1, header_col2 = st.columns([3, 2], vertical_alignment="center")

with header_col1:
    st.markdown(
        '<div class="app-title-block">'
        "<h1>🥗 MacroSnap</h1>"
        "<p>Your AI nutrition buddy</p>"
        "</div>",
        unsafe_allow_html=True,
    )

with header_col2:
    twilio_ready = _check_twilio_secrets()
    can_send = st.session_state.meal_discussed and twilio_ready

    if not twilio_ready:
        wa_tooltip = "Twilio credentials not configured in secrets"
    elif not st.session_state.meal_discussed:
        wa_tooltip = "Discuss at least one meal first to generate a summary"
    else:
        wa_tooltip = f"Send nutrition summary to {st.session_state.user_phone}"

    send_clicked = st.button(
        "📤 Send to WhatsApp",
        disabled=not can_send,
        use_container_width=True,
        help=wa_tooltip,
    )

# ── Handle WhatsApp send action ─────────────────────────────────────
if send_clicked:
    with st.spinner("Generating summary & dispatching via Twilio WhatsApp…"):
        # Ask Gemini for the summary
        try:
            summary_response = st.session_state.chat.send_message(SUMMARY_PROMPT)
            raw_summary = summary_response.text
        except Exception:
            raw_summary = ""

        summary = clean_whatsapp_text(raw_summary)

        success, detail = send_whatsapp(
            st.session_state.user_phone,
            st.session_state.user_name,
            summary,
        )

    if success:
        st.success(
            f"✅ Nutrition summary dispatched to **{st.session_state.user_phone}** via WhatsApp!\n\n"
            f"*Message SID: `{detail}`*"
        )
    else:
        st.error(f"❌ {detail}")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Render existing conversation ────────────────────────────────────
for msg in st.session_state.messages:
    render_message(msg)

# ── Chat input ──────────────────────────────────────────────────────
user_input = st.chat_input(
    "Describe a meal or upload a photo…",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    # Extract text and file from the ChatInputValue
    user_text = user_input.text if hasattr(user_input, "text") else None
    user_file = None

    # st.chat_input with accept_file returns a ChatInputValue object
    if hasattr(user_input, "files") and user_input.files:
        user_file = user_input.files[0]
    elif hasattr(user_input, "file") and user_input.file:
        user_file = user_input.file

    # If there's no file component, user_input might just be a string
    if not user_text and isinstance(user_input, str):
        user_text = user_input

    # ── Validate: at least something was provided ───────────────
    has_text = bool(user_text and user_text.strip())
    has_image = user_file is not None

    if not has_text and not has_image:
        st.stop()

    # ── Build parts for Gemini & display messages ───────────────
    gemini_parts = []

    # Show and record the user's text
    if has_text:
        add_message("user", user_text.strip())
        with st.chat_message("user"):
            st.markdown(user_text.strip())
        gemini_parts.append(user_text.strip())

    # Show and record the uploaded image
    if has_image:
        image_bytes = user_file.read()
        mime_type = user_file.type if hasattr(user_file, "type") else "image/jpeg"

        # Validate mime type
        if mime_type not in ALLOWED_IMAGE_TYPES:
            st.warning("Please upload a JPG, JPEG, or PNG image.")
            st.stop()

        add_message("user", image_bytes, kind="image")
        with st.chat_message("user"):
            st.image(image_bytes, use_container_width=True)

        # Create Gemini image part
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        gemini_parts.append(image_part)

        # If no text was provided with the image, use the default prompt
        if not has_text:
            gemini_parts.append(DEFAULT_IMAGE_PROMPT)

    # ── Call Gemini ─────────────────────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("Analysing…"):
            reply = ask_gemini(gemini_parts)
        st.markdown(reply)

    add_message("assistant", reply)

    # Mark that at least one meal has been discussed
    st.session_state.meal_discussed = True
    st.rerun()
