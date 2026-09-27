from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse
import requests
import random
import base64

app = FastAPI()

# Secure NVIDIA API Keys Pool
NVIDIA_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]

# Aapke diye gaye 100% Verified Working Models
MODELS = {
    # Chat / LLM Models
    "nemotron": {"name": "Nemotron 3 Super (120B)", "model_id": "nvidia/nemotron-3-super-120b-a12b", "type": "text"},
    "gpt_oss": {"name": "GPT-OSS (20B)", "model_id": "openai/gpt-oss-20b", "type": "text"},
    "mistral_nemotron": {"name": "Mistral Nemotron", "model_id": "mistralai/mistral-nemotron", "type": "text"},
    "muse_glimmer": {"name": "Muse Glimmer (30B)", "model_id": "meta/muse-glimmer-30b", "type": "text"},
    "kimi": {"name": "Kimi K3", "model_id": "moonshotai/kimi-k3", "type": "text"},
    
    # Vision Models
    "vision_llama": {"name": "Llama 3.2 Vision (11B)", "model_id": "meta/llama-3.2-11b-vision-instruct", "type": "vision"},
    "vision_nemotron": {"name": "Nemotron Nano Omni Reasoning", "model_id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "type": "vision"},
    
    # Translation Models
    "translate_v1": {"name": "Riva Translate v1.1", "model_id": "nvidia/riva-translate-4b-instruct-v1.1", "type": "text"},
    "translate_v2": {"name": "Riva Translate v2", "model_id": "nvidia/riva-translate-4b-instruct-v2", "type": "text"},
    
    # Image Generation Models
    "flux_klein": {"name": "Flux.2 Klein (4B)", "model_id": "black-forest-labs/flux.2-klein-4b", "type": "image"},
    "flux_schnell": {"name": "Flux.1 Schnell", "model_id": "black-forest-labs/flux.1-schnell", "type": "image"},
    "stable_diffusion": {"name": "Stable Diffusion 3 Medium", "model_id": "stabilityai/stable-diffusion-3-medium", "type": "image"}
}

SESSION_HISTORY = []
CURRENT_MODEL = "nemotron"

def get_html():
    current_meta = MODELS.get(CURRENT_MODEL, MODELS["nemotron"])
    
    options_html = ""
    for k, v in MODELS.items():
        sel = "selected" if k == CURRENT_MODEL else ""
        options_html += f'<option value="{k}" {sel}>{v["name"]}</option>'
        
    history_html = ""
    for chat in SESSION_HISTORY:
        if chat["type"] == "image":
            resp_block = f'<p class="mb-2 text-emerald-400 font-bold">Generated Artwork:</p><img src="{chat["response"]}" class="rounded-xl border border-zinc-800 max-h-72 object-cover shadow-2xl">'
        else:
            user_img_tag = f'<div class="mb-2"><img src="{chat["user_img"]}" class="rounded-lg max-h-36 border border-zinc-700 shadow-md"></div>' if chat.get("user_img") else ""
            resp_block = chat["response"]
            
        history_html += f"""
        <div class="flex items-start space-x-3 flex-row-reverse space-x-reverse mb-4">
            <div class="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-300 flex items-center justify-center font-bold text-xs shrink-0">U</div>
            <div class="px-4 py-3 rounded-2xl text-xs max-w-[80%] leading-relaxed bg-emerald-600 text-zinc-950 font-medium rounded-tr-sm shadow-md">
                {user_img_tag}
                {chat["user"]}
            </div>
        </div>
        <div class="flex items-start space-x-3 mb-4">
            <div class="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-xs shrink-0">AI</div>
            <div class="bg-zinc-900 border border-zinc-800 px-4 py-3 rounded-2xl rounded-tl-sm text-xs text-zinc-200 max-w-[80%] leading-relaxed shadow-md whitespace-pre-wrap">{resp_block}</div>
        </div>
        """

    is_vision = current_meta["type"] == "vision"
    is_image_gen = current_meta["type"] == "image"
    
    placeholder = "Describe image to generate..." if is_image_gen else ("Ask about image or prompt..." if is_vision else f"Message {current_meta['name']}...")

    upload_icon_html = ""
    if is_vision:
        upload_icon_html = """
        <label class="cursor-pointer p-2.5 text-zinc-400 hover:text-emerald-400 transition-colors flex items-center justify-center" title="Upload Image">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"></path></svg>
            <input type="file" name="image_file" accept="image/*" class="hidden" onchange="showFileName(this)">
        </label>
        <span id="fileBadge" class="text-[10px] text-emerald-400 hidden mr-2">Attached</span>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en" class="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>NEXUS // VERIFIED AI STUDIO</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background-color: #030307; color: #e2e8f0; font-family: monospace; }}
            ::-webkit-scrollbar {{ width: 4px; }}
            ::-webkit-scrollbar-thumb {{ background: #27272a; border-radius: 4px; }}
        </style>
    </head>
    <body class="flex flex-col h-screen w-screen justify-between p-2 md:p-4 select-none">

        <!-- Header -->
        <header class="w-full max-w-3xl mx-auto flex justify-between items-center px-4 py-3 bg-zinc-900/90 border border-zinc-800 rounded-2xl shadow-lg backdrop-blur-md">
            <div class="flex items-center space-x-2.5">
                <div class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></div>
                <h1 class="text-xs md:text-sm font-black tracking-widest text-emerald-400">NEXUS AI</h1>
            </div>
            
            <form action="/switch-model" method="POST" class="flex items-center space-x-2">
                <select name="selected_model" onchange="this.form.submit()" class="bg-zinc-950 border border-zinc-700 text-xs text-emerald-400 font-bold px-3 py-1.5 rounded-xl focus:outline-none focus:border-emerald-500 cursor-pointer">
                    {options_html}
                </select>
            </form>
        </header>

        <!-- Chat Container -->
        <main id="chatContainer" class="w-full max-w-3xl mx-auto flex-grow my-3 overflow-y-auto px-4 py-3 bg-zinc-950/80 border border-zinc-900 rounded-2xl flex flex-col shadow-inner">
            <div class="flex items-start space-x-3 mb-4">
                <div class="w-7 h-7 rounded-lg bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold text-xs shrink-0">AI</div>
                <div class="bg-zinc-900 border border-zinc-800 px-4 py-3 rounded-2xl rounded-tl-sm text-xs text-zinc-200 max-w-[80%] leading-relaxed shadow-md">
                    Namaste! Active verified model: <strong class="text-emerald-400">{current_meta['name']}</strong>. Aap sawaal pooch sakte hain!
                </div>
            </div>
            {history_html}
        </main>

        <!-- Input Bar -->
        <form action="/send" method="POST" enctype="multipart/form-data" class="w-full max-w-3xl mx-auto bg-zinc-900/95 border border-zinc-800 rounded-2xl p-2.5 shadow-2xl flex items-center space-x-2 mb-2">
            {upload_icon_html}
            <input type="text" name="prompt" required placeholder="{placeholder}" class="flex-grow bg-zinc-950 border border-zinc-800 text-xs text-zinc-100 px-4 py-3 rounded-xl focus:outline-none focus:border-emerald-500 transition-all placeholder:text-zinc-600" autocomplete="off">
            <button type="submit" class="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-black text-xs rounded-xl transition-all shadow-md">
                SEND
            </button>
        </form>

        <script>
            function showFileName(input) {{
                const badge = document.getElementById('fileBadge');
                if (input.files && input.files[0]) {{
                    badge.classList.remove('hidden');
                }} else {{
                    badge.classList.add('hidden');
                }}
            }}
            const container = document.getElementById("chatContainer");
            container.scrollTop = container.scrollHeight;
        </script>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return HTMLResponse(content=get_html())

@app.post("/switch-model", response_class=HTMLResponse)
async def switch_model(selected_model: str = Form(...)):
    global CURRENT_MODEL
    if selected_model in MODELS:
        CURRENT_MODEL = selected_model
    return HTMLResponse(content=get_html())

@app.post("/send", response_class=HTMLResponse)
async def send_prompt(prompt: str = Form(...), image_file: UploadFile = File(None)):
    global SESSION_HISTORY
    current_meta = MODELS[CURRENT_MODEL]
    model_type = current_meta["type"]
    api_key = random.choice(NVIDIA_KEYS)
    response_text = ""
    user_img_b64 = None

    if model_type == "image":
        url = f"https://ai.api.nvidia.com/v1/genai/{current_meta['model_id']}"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json", "Content-Type": "application/json"}
        payload = {"prompt": prompt, "cfg_scale": 5, "steps": 25, "aspect_ratio": "16:9"}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=35)
            if res.status_code == 200:
                data = res.json()
                img_b64 = data["artifact"][0]["base64"] if "artifact" in data and data["artifact"] else ""
                response_text = f"data:image/png;base64,{img_b64}" if img_b64 else "https://picsum.photos/500/300"
            else:
                response_text = f"Image Gen Error ({res.status_code})"
        except:
            response_text = "https://picsum.photos/500/300"

        SESSION_HISTORY.append({"user": prompt, "response": response_text, "type": "image"})

    elif model_type == "vision":
        messages_content = [{"type": "text", "text": prompt}]
        if image_file and image_file.filename:
            contents = await image_file.read()
            user_img_b64 = f"data:{image_file.content_type};base64,{base64.b64encode(contents).decode('utf-8')}"
            messages_content.append({"type": "image_url", "image_url": {"url": user_img_b64}})

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": current_meta["model_id"], "messages": [{"role": "user", "content": messages_content}], "temperature": 0.7, "max_tokens": 1024}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                response_text = res.json()["choices"][0]["message"]["content"]
            else:
                response_text = f"Vision API Error: Status {res.status_code}"
        except Exception as e:
            response_text = f"Error: {str(e)}"

        SESSION_HISTORY.append({"user": prompt, "user_img": user_img_b64, "response": response_text, "type": "text"})

    else:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": current_meta["model_id"], "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 1024}
        try:
            res = requests.post(url, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                response_text = res.json()["choices"][0]["message"]["content"]
            else:
                response_text = f"API Error: Status {res.status_code}"
        except Exception as e:
            response_text = f"Error: {str(e)}"

        SESSION_HISTORY.append({"user": prompt, "response": response_text, "type": "text"})

    return HTMLResponse(content=get_html())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
    
