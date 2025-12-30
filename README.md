# ImmersiveReading

PARTIALLY DEPRECATED

## Installation (SD 1.5 + LatentLabs 360 LoRA)

Create venv, activate it & install requirements.txt

### Scene Deconstructor LLM

1. install ollama

2. pull GPT Open Source model `ollama pull gpt-oss:20b`

### Image Generation

1. Install Python 3.10

2. Install Stable Diffustion AUTOMATIC1111 WebUI
``` 
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffustion-webui
```

3. Modify `stable-diffusion-webui/webui-user.bat` as follows:
- ```set PYTHON=C:\Path_to_Python\Python310\python.exe```
- ```set COMMANDLINE_ARGS=--xformers --api```

4. Download Base Model (SD 1.5-compatible), e.g [DreamShaper](https://civitai.com/models/4384?modelVersionId=6202) and put it in `stable-diffusion-webui/models/Stable-diffusion`

5. Start WebUI and select Base Model
- powershell: `.\webui-user.bat`
- bash: `webui-user.bat`

6. Install WebUI Extensions (Additional Networks for LoRA + Asymmetric Tiling for reducing seams)
- Navigate to **Extensions** Tab > Install from URL
- enter `https://github.com/kohya-ss/sd-webui-additional-networks` & click install
- enter `https://github.com/tjm35/asymmetric-tiling-sd-webui` & click install
- Navigate to **Extensions** Tab > Installed
- Click **Apply and restart UI**

7. Download [LatentLabs 360 LoRA](https://civitai.com/models/10753/latentlabs360) and put it in 
- `stable-diffusion-webui/models/Stable-diffusion/models/Lora` (create Lora folder if it doesn't exist)
- `stable-diffusion-webui/extensions/sd-webui-additional-networks/models/lora`

8. Select Base Model in WebUI (top left corner)

## Execution

```python main.py```





