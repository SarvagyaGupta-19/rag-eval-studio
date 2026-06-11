import base64
from pathlib import Path

img_path = r"c:\Users\sarva\Downloads\Rag Evals\download.jpg"
css_path = r"c:\Users\sarva\Downloads\Rag Evals\rag-eval-studio\app\styles.css"

with open(img_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

css_content = f"""
/* 
  Finance Insights CSS
  Dark Theme, Custom Background, Grid Animation
*/

@import url('https://fonts.googleapis.com/css2?family=Helvetica+Neue:wght@400;500;600;700&display=swap');

/* Base */
html, body, [class*="css"] {{
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif !important;
    color: #e2e8f0 !important;
}}

/* Set the custom background image */
.stApp {{
    background-image: url("data:image/jpeg;base64,{encoded}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}}

/* Add a slight dark overlay to the app to ensure text is readable */
.stApp::before {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(10, 15, 30, 0.7); /* Dark overlay */
    z-index: 0;
    pointer-events: none;
}}

/* Ensure main blocks stay above the overlay */
.block-container {{
    position: relative;
    z-index: 1;
}}

/* Hide Streamlit elements */
#MainMenu, header, footer, .stDeployButton {{
    visibility: hidden;
    display: none;
}}

/* Sidebar styling (Glassmorphism) */
[data-testid="stSidebar"] {{
    background: rgba(15, 23, 42, 0.4) !important;
    backdrop-filter: blur(16px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}}

/* Header text */
h1, h2, h3, h4, h5, h6 {{
    color: #f8fafc !important;
    font-weight: 600 !important;
}}

/* Landing Page Centering */
.landing-header {{
    text-align: center;
    margin-top: 15vh;
}}
.landing-header h2 {{
    font-size: 48px !important;
    margin-bottom: 12px !important;
    text-shadow: 0 4px 20px rgba(0,0,0,0.5);
}}
.landing-header p {{
    color: #cbd5e1 !important;
    font-size: 18px !important;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}}

/* Chat Bubbles */
[data-testid="stChatMessage"] {{
    background-color: transparent !important;
    padding: 1rem 0 !important;
    border: none !important;
}}

/* User Message */
[data-testid="stChatMessage"]:nth-child(even) {{
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px;
    padding: 1rem !important;
}}

/* Chat Input Area (Glassmorphism) */
[data-testid="stChatInput"] {{
    background: rgba(15, 23, 42, 0.6) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 16px !important;
    padding: 4px !important;
}}

[data-testid="stChatInput"] textarea {{
    color: #f8fafc !important;
    font-size: 15px !important;
}}

/* File Uploader styling */
[data-testid="stFileUploader"] {{
    background: rgba(30, 41, 59, 0.4);
    border: 1px dashed rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    padding: 1rem;
}}

/* Source Citation Pills */
.source-pill {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: rgba(51, 65, 85, 0.6);
    backdrop-filter: blur(4px);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 6px;
    cursor: pointer;
}}
.source-pill:hover {{
    background: rgba(71, 85, 105, 0.8);
    border-color: rgba(255, 255, 255, 0.3);
}}

/* Grid Dots Moving Animation for Thinking State */
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
    background-color: #4d8eff;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulseGrid 1.5s infinite ease-in-out both;
}}

.grid-dot:nth-child(1) {{ animation-delay: -0.32s; }}
.grid-dot:nth-child(2) {{ animation-delay: -0.16s; }}
.grid-dot:nth-child(3) {{ animation-delay: 0s; }}

@keyframes pulseGrid {{
    0%, 80%, 100% {{ transform: scale(0); opacity: 0.3; }}
    40% {{ transform: scale(1); opacity: 1; box-shadow: 0 0 10px #4d8eff; }}
}}

.thinking-text {{
    color: #cbd5e1;
    font-size: 14px;
    margin-left: 8px;
    font-style: italic;
}}
"""

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css_content)

print("CSS updated successfully!")
