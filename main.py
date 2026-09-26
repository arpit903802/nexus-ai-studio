from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import requests
import random
import base64

app = FastAPI()

# Aapki di gayi 6 NVIDIA API Keys ka Secure Pool
NVIDIA_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

# Supported Models Configuration
MODELS = {
    "llama70b": {"name": "Nexus Intelligence (Llama 3.1 70B)", "model_id": "meta/llama-3.1-70b-instruct", "type": "text"},
    "vision": {"name": "Nexus Vision Studio (Llama 3.2 90B Vision)", "model_id": "meta/llama-3.2-90b-vision-instruct", "type": "vision"},
    "mistral": {"name": "Nexus Reasoning (Mistral Large)", "model_id": "mistralai/mistral-large-2-instruct", "type": "text"},
    "image_gen": {"name": "Nexus Image Studio (Stable Diffusion 3)", "model_id": "stabilityai/stable-diffusion-3-medium", "type": "image"}
}

SESSION_HISTORY = []
CURRENT_MODEL = "llama70b"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>NEXUS // ENTERPRISE AI STUDIO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #020205; color: #e2e8f0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; overflow: hidden; }
        .glass-panel { background: rgba(9, 9, 15, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.08); }
        .glow-effect { box-shadow: 0 0 50px rgba(16, 185, 129, 0.06); }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #020205; }
        ::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }
    </style>
</head>
<body class="flex flex-col h-screen w-screen select-none justify-between p-2 md:p-5 pb-4">

    <!-- Top Navigation Bar -->
    <header class="w-full max-w-4xl mx-auto flex flex-col md:flex-row justify-between items-center px-5 py-3 glass-panel rounded-2xl shadow-2xl gap-3 z-10">
        <div class="flex items-center space-x-3">
            <div class="relative flex items-center justify-center">
                <div class="w-3 h-3 bg-emerald-500 rounded-full animate-ping absolute"></div>
                <div class="w-3 h-3 bg-emerald-400 rounded-full"></div>
            </div>
            <div>
                <h1 class="text-xs md:text-sm font-black tracking-widest text-emerald-400">NEXUS // CORE</h1>
                <p class="text-[9px] text-zinc-500 tracking-wider">SECURE NIM CLUSTER ACTIVE</p>
            </div>
        </div>
        
        <!-- Model Selector Form -->
        <form action="/switch-model" method="POST" class="flex items-center space-x-2 bg-zinc-950/80 px-3 py-1.5 rounded-xl border border-zinc-800">
            <span class="text-[10px] text-zinc-400 font-bold uppercase tracking-wider">Engine:</span>
            <select name="selected_model" onchange="this.form.submit()" class="bg-transparent text-xs text-emerald-400 font-bold focus:outline-none cursor-pointer">
                {{ options_html | safe }}
            </select>
        </form>
    </header>

    <!-- Main Output / Chat Arena -->
    <main id="chatContainer" class="w-full max-w-4xl mx-auto flex-grow my-3 overflow-y-auto px-4 py-4 space-y-5 glass-panel rounded-2xl glow-effect flex flex-col">
        <div class="flex items-start space-x-3 animate-fade-in">
            <div class="w-8 h-8 rounded-xl bg-emerald-600/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs shrink-0 shadow-lg">AI</div>
            <div class="glass-panel px-4 py-3 rounded-2xl rounded-tl-sm text-xs text-zinc-200 max-w-[85%] leading-relaxed shadow-xl border border-zinc-800/80">
                Welcome to Nexus Enterprise Studio. Current active model: <strong class="text-emerald-400">{{ model_display_name }}</strong>. 
                {% if current_model == 'vision' %}
                <span class="block mt-1 text-cyan-400 font-semibold">⚡ Vision Mode Enabled: You can upload an image and ask questions about it!</span>
                {% elif current_model == 'image_gen' %}
                <span class="block mt-1 text-amber-400 font-semibold">🎨 Image Generation Mode: Describe any artwork to generate high-res visuals.</span>
                {% else %}
                <span class="block mt-1 text-zinc-400">Ask complex technical questions, request code, or analyze research data.</span>
                {% endif %}
            </div>
        </div>
        
        {{ history_html | safe }}
    </main>

    <!-- Interactive Input Bar -->
    <form action="/send" method="POST" enctype="multipart/form-data" class="w-full max-w-4xl mx-auto glass-panel rounded-2xl p-3 shadow-2xl backdrop-blur-xl flex flex-col gap-2 mb-2">
        
        <!-- File Upload Preview Row (Visible only in Vision Mode) -->
        {% if current_model == 'vision' %}
        <div class="flex items-center space-x-2 px-2 py-1 bg-zinc-950/60 rounded-xl border border-zinc-800/80 text-[11px]">
            <label class="cursor-pointer bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded-lg font-bold transition-all flex items-center space-x-1.5">
                <span>📁 Upload Image</span>
                <input type="file" name="image_file" accept="image/*" class="hidden" onchange="updateFileName(this)">
            </label>
            <span id="fileNameDisplay" class="text-zinc-400 truncate italic">No image selected (Optional)</span>
        </div>
        {% endif %}

        <!-- Input Text & Send Button -->
        <div class="flex items-center space-x-2">
            <input type="text" name="prompt" required placeholder="{{ placeholder_text }}" class="flex-grow bg-zinc-950/90 border border-zinc-800 text-xs text-zinc-100 px-4 py-3.5 rounded-xl focus:outline-none focus:border-emerald-500 transition-all placeholder:text-zinc-600 shadow-inner" autocomplete="off">
            <button type="submit" class="px-6 py-3.5 bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-zinc-950 font-black text-xs tracking-wider rounded-xl transition-all shadow-lg shadow-emerald-950/50 cursor-pointer">
                {{ button_text }}
            </button>
        </div>
    </form>

    <script>
        function updateFileName(input) {
            const display = document.getElementById('fileNameDisplay');
            if (input.files && input.files[0]) {
                display.innerText = input.files[0].name;
                display.classList.add("text-emerald-400");
            } else {
                display.innerText = "No image selected (Optional)";
                display.classList.remove("text-emerald-400");
            }
        }
        
        // Auto scroll to bottom
        const container = document.getElementById("chatContainer");
        container.scrollTop = container.scrollHeight;
    </script>
</body>
</html>
"""

def render_page():
    current_meta = MODELS.get(CURRENT_MODEL, MODELS["llama70b"])
    model_name = current_meta["name"]
    is_img = current_meta["type"] == "image"
    is_vision = current_meta["type"] == "vision"
    
    options_html = ""
    for k, v in MODELS.items():
        sel = "selected" if k == CURRENT_MODEL else ""
        options_html += f'<option value="{k}" {sel}>{v["name"]}</option>'
        
    history_html = ""
    for chat in SESSION_HISTORY:
        if chat["type"] == "image":
            resp_block = f'<p class="mb-2 text-emerald-400 font-bold">Generated Visual Artwork:</p><img src="{chat["response"]}" class="rounded-xl border border-zinc-800 max-h-72 object-cover shadow-2xl">'
        else:
            user_img_tag = f'<div class="mb-2"><img src="{chat["user_img"]}" class="rounded-lg max-h-40 border border-zinc-700 shadow-md"></div>' if chat.get("user_img") else ""
            resp_block = chat["response"]
            
        history_html += f'''
        <div class="flex items-start space-x-3 flex-row-reverse space-x-reverse">
            <div class="w-8 h-8 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-300 flex items-center justify-center font-bold text-xs shrink-0 shadow">U</div>
            <div class="px-4 py-3 rounded-2xl text-xs max-w-[85%] leading-relaxed shadow-xl bg-emerald-600 text-zinc-950 font-medium rounded-tr-sm">
                {user_img_tag if 'user_img' in chat else ''}
                {chat["user"]}
            </div>
        </div>
        <div class="flex items-start space-x-3">
            <div class="w-8 h-8 rounded-xl bg-emerald-600/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-xs shrink-0 shadow">AI</div>
            <div class="glass-panel px-4 py-3 rounded-2xl rounded-tl-sm text-xs text-zinc-200 max-w-[85%] leading-relaxed shadow-xl border border-zinc-800/80 whitespace-pre-wrap">{resp_block}</div>
        </div>
        '''

    if is_img:
        placeholder = "Describe artwork to generate (e.g., Cyberpunk Tokyo street at night)..."
        btn_txt = "GENERATE"
    elif is_vision:
        placeholder = "Ask anything about the uploaded image or prompt..."
        btn_txt = "ANALYZE"
    else:
        placeholder = f"Ask anything to {model_name}..."
        btn_txt = "EXECUTE"

    page = HTML_TEMPLATE
    page = page.replace('{{ options_html | safe }}', options_html)
    page = page.replace('{{ model_display_name }}', model_name)
    page = page.replace('{{ current_model }}', CURRENT_MODEL)
    page = page.replace('{{ history_html | safe }}', history_html)
    page = page.replace('{{ placeholder_text }}', placeholder)
    page = page.replace('{{ button_text }}', btn_txt)
    return page

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return HTMLResponse(content=render_page())

@app.post("/switch-model", response_class=HTMLResponse)
async def switch_model(selected_model: str = Form(...)):
    global CURRENT_MODEL
    if selected_model in MODELS:
        CURRENT_MODEL = selected_model
    return HTMLResponse(content=render_page())

@app.post("/send", response_class=HTMLResponse)
async def send_prompt(prompt: str = Form(...), image_file: UploadFile = File(None)):
    global SESSION_HISTORY
    current_meta = MODELS[CURRENT_MODEL]
    model_type = current_meta["type"]
    
    api_key = random.choice(NVIDIA_KEYS)
    response_text = ""
    user_img_b64 = None

    if model_type == "image":
        # Stable Diffusion 3 Medium Generation
        url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "cfg_scale": 5,
            "steps": 25,
            "aspect_ratio": "16:9"
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=35)
            if res.status_code == 200:
                data = res.json()
                if "artifact" in data and len(data["artifact"]) > 0:
                    img_b64 = data["artifact"][0]["base64"]
                    response_text = f"data:image/png;base64,{img_b64}"
                else:
                    response_text = "https://picsum.photos/600/350"
            else:
                response_text = f"Generation Error ({res.status_code}). Please retry."
        except Exception:
            response_text = "Connection timeout during image generation."

        SESSION_HISTORY.append({
            "user": prompt,
            "response": response_text,
            "type": "image"
        })

    elif model_type == "vision":
        # Handle Image Upload & Multimodal Vision Query
        messages_content = [{"type": "text", "text": prompt}]
        
        if image_file and image_file.filename:
            contents = await image_file.read()
            user_img_b64 = f"data:{image_file.content_type};base64,{base64.b64encode(contents).decode('utf-8')}"
            messages_content.append({
                "type": "image_url",
                "image_url": {"url": user_img_b64}
            })

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": current_meta["model_id"],
            "messages": [{"role": "user", "content": messages_content}],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=35)
            if res.status_code == 200:
                data = res.json()
                response_text = data["choices"][0]["message"]["content"]
            else:
                response_text = f"Vision API Error: Status {res.status_code}"
        except Exception as e:
            response_text = f"Error processing vision request: {str(e)}"

        SESSION_HISTORY.append({
            "user": prompt,
            "user_img": user_img_b64,
            "response": response_text,
            "type": "text"
        })

    else:
        # Standard Text Chat Models (Llama 70B / Mistral Large)
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": current_meta["model_id"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1024
        }
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                response_text = data["choices"][0]["message"]["content"]
            else:
                response_text = f"API Error: Status code {res.status_code}."
        except Exception as e:
            response_text = f"Connection error: {str(e)}"

        SESSION_HISTORY.append({
            "user": prompt,
            "response": response_text,
            "type": "text"
        })
    
    return HTMLResponse(content=render_page())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
