import base64
from pathlib import Path

img_path = r"c:\Users\sarva\Downloads\Rag Evals\Interstellar wallpaper 4k.jpg"
css_path = r"c:\Users\sarva\Downloads\Rag Evals\rag-eval-studio\app\styles.css"

with open(img_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

css_content = f"""
/* 
  Finance Insights CSS
  Senior UI/UX Improvements - Interstellar Theme
*/

@import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@300;400;500;600;700&display=swap');

/* Base */
html, body, [class*="css"] {{
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important;
    color: #f1f5f9 !important;
}}

/* Set the custom background image globally */
.stApp, .stApp > header {{
    background-color: transparent !important;
    background-image: url("data:image/jpeg;base64,{encoded}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

/* Add a global dark overlay for readability */
.stApp::before {{
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at center, rgba(15,23,42,0.4) 0%, rgba(2,6,23,0.85) 100%);
    z-index: 0;
    pointer-events: none;
}}

.block-container {{
    position: relative;
    z-index: 1;
}}

/* Hide Streamlit elements */
#MainMenu, header, footer, .stDeployButton {{
    visibility: hidden;
    display: none;
}}

/* Transparent Sidebar with Glassmorphism */
[data-testid="stSidebar"] {{
    background-color: rgba(15, 23, 42, 0.3) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}}

/* Fix for Sidebar interior background */
[data-testid="stSidebar"] > div:first-child {{
    background-color: transparent !important;
}}

/* Header text */
h1, h2, h3, h4, h5, h6 {{
    color: #ffffff !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}}

/* Premium Landing Page Centering */
.landing-header {{
    text-align: center;
    margin-top: 20vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}
.landing-header h2 {{
    font-size: 56px !important;
    margin-bottom: 8px !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em;
    background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}
.landing-header p {{
    color: #94a3b8 !important;
    font-size: 18px !important;
    font-weight: 300 !important;
    max-width: 600px;
    line-height: 1.6;
    text-shadow: 0 4px 10px rgba(0,0,0,0.5);
}}

/* Chat Bubbles */
[data-testid="stChatMessage"] {{
    background-color: transparent !important;
    padding: 1rem 0 !important;
    border: none !important;
}}

/* User Message */
[data-testid="stChatMessage"]:nth-child(even) {{
    background: rgba(30, 41, 59, 0.5) !important;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 16px;
    padding: 1.2rem !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}}

/* Chat Input Area (Bottom container fix) */
.stChatFloatingInputContainer {{
    background-color: transparent !important;
    padding-bottom: 20px;
}}

[data-testid="stChatInput"] {{
    background: rgba(15, 23, 42, 0.7) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 24px !important;
    padding: 6px 12px !important;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4) !important;
}}

[data-testid="stChatInput"] textarea {{
    color: #ffffff !important;
    font-size: 16px !important;
}}

[data-testid="stChatInput"] button {{
    background-color: #3b82f6 !important;
    border-radius: 50% !important;
    color: #ffffff !important;
    transition: all 0.2s ease;
}}

[data-testid="stChatInput"] button:hover {{
    background-color: #60a5fa !important;
    transform: scale(1.05);
}}

/* File Uploader styling */
[data-testid="stFileUploader"] {{
    background: rgba(30, 41, 59, 0.3);
    border: 1px dashed rgba(255, 255, 255, 0.15);
    border-radius: 12px;
    padding: 1rem;
    transition: all 0.2s ease;
}}
[data-testid="stFileUploader"]:hover {{
    background: rgba(30, 41, 59, 0.5);
    border-color: rgba(255, 255, 255, 0.3);
}}

/* Source Citation Pills */
.source-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(51, 65, 85, 0.4);
    backdrop-filter: blur(8px);
    color: #cbd5e1;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    margin-right: 8px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
}}
.source-pill:hover {{
    background: rgba(71, 85, 105, 0.8);
    border-color: rgba(255, 255, 255, 0.3);
    transform: translateY(-1px);
}}

/* Grid Dots Moving Animation */
.grid-dots-container {{
    display: flex;
    justify-content: flex-start;
    align-items: center;
    padding: 10px 0;
    height: 40px;
}}

.grid-dot {{
    width: 8px;
    height: 8px;
    background-color: #60a5fa;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulseGrid 1.5s infinite ease-in-out both;
}}

.grid-dot:nth-child(1) {{ animation-delay: -0.32s; }}
.grid-dot:nth-child(2) {{ animation-delay: -0.16s; }}
.grid-dot:nth-child(3) {{ animation-delay: 0s; }}

@keyframes pulseGrid {{
    0%, 80%, 100% {{ transform: scale(0); opacity: 0.3; }}
    40% {{ transform: scale(1); opacity: 1; box-shadow: 0 0 12px #60a5fa; }}
}}

.thinking-text {{
    color: #94a3b8;
    font-size: 14px;
    font-style: italic;
    font-weight: 300;
}}
"""

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css_content)

print("CSS updated successfully!")
