# GENIE - Generative Narrative Immersion Engine

Welcome to the repository for **GENIE: Generative Narrative Immersion Engine for Deep Reading Engagement**.
It contains the system implementation described in our paper. This work is open-source for academic and non-commercial use only.

TODO: Paste abstract

## Project Structure

The project consists of two main parts: The Python application for content generation (`genie_python`) and the Unity VR Application for displaying the generated content (`genie_vr`).

## Prerequisites

For a successful system setup, make sure the following prerequisites are met:

* Meta Quest HMD (project has only been tested on MQ 3, but should work on other versions as well)
* Meta Quest Link ([Developer Setup](https://developers.meta.com/horizon/documentation/unity/unity-link/#set-up-link))
* Unity Hub and Unity 6000.2.15f (with Android Build Support)
* Python 3.10 + pip
* at least one of the following:
  * OpenAI API keys
  * Ollama


## Python Application

If you do not wish to generate custom book content, but only want to view the sample data, you can skip steps 2 to 4.

If you only want to generate content, you will only need to follow steps 1 to 4.

### 1. Virtual Environment Preparation

Windows
```
cd genie_python
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```
Linux / macOS
```
cd genie_python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure LLM
You can either use a GPT model from the OpenAI cloud or a local open souce GPT model with ollama. 

**OpenAI Cloud**

`config.py`
```
USE_OPENAI_API = True
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-5.1" // or other
```

Create a `.env` file in the `genie_python` dict and enter your API Key.

`.env`
```
OPENAI_API_KEY=your_api_key_here
```

**Ollama**

`config.py`
```
USE_OPENAI_API = False
```

Run the following commands in the terminal:
```
ollama pull gpt-oss:20b
// or
ollama pull gpt-oss:120b
```

### 3. Stable Diffusion WebUI

**3.1** Clone Stable Diffustion AUTOMATIC1111 WebUI project:
``` 
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
cd stable-diffustion-webui
```

**3.2** Modify `stable-diffusion-webui/webui-user.bat` as follows:
```
set PYTHON=C:\Path_to_Python\Python310\python.exe
set COMMANDLINE_ARGS=--xformers --api
```

**3.3** Download Base Model (SD 1.5-compatible), e.g [DreamShaper](https://civitai.com/models/4384?modelVersionId=6202) and paste it to `stable-diffusion-webui/models/Stable-diffusion`

**3.4** Start WebUI by executing the script `webui-user.bat`.

**3.5** Select SD 1.5 Base Model in the top left corner.

**3.6** Install WebUI Extensions (Additional Networks for LoRA + Asymmetric Tiling for reducing seams)
1. Navigate to **Extensions** Tab > Install from URL
2. enter `https://github.com/kohya-ss/sd-webui-additional-networks` & click install
3. enter `https://github.com/tjm35/asymmetric-tiling-sd-webui` & click install
4. Navigate to **Extensions** Tab > Installed
5. Click **Apply and restart UI**

**3.7** Download [LatentLabs 360 LoRA](https://civitai.com/models/10753/latentlabs360) and put it in 
- `stable-diffusion-webui/models/Lora` (create Lora folder if it doesn't exist)

### 4. Run Scene Generation

**4.1** Create folder for raw book files and add a `.txt` file containing book text. It is recommended to remove title, preface and appendix of the text.
```
mkdir raw_books
```
**4.2** Execute Generation Script
```
python generate_vrbook.py <path-to-book-file.txt> <book-title> [<author>]
```

### (4a. Regenerate Images)

For regenerating images for existing image prompts, execute
```
python generate_vrbook.py --regenerate-imgs <book-id>
```

### (4b. Generate Prompts only)
For generating image prompts from book text only, execute
```
python generate_vrbook.py --prompts-only <path-to-book-file.txt> <book-title> [<author>]
```

### 5. Content Server
The content server provides an API for fetching generated content from the previously filled database.

Start the server by executing
```
uvicorn server:app
```

## VR Application

1. Import `genie_vr` as a new project in Unity Hub and open it
2. Click `Yes` on all Popups
3. Follow [this](https://developers.meta.com/horizon/documentation/unity/unity-tutorial-hello-vr/) tutorial to correctly setup the project
4. Open `Scenes/ReadingScene` and import `TMP Essentials` when the popup opens
4. With Link activated on Meta Quest HMD, start Unity Play Mode
5. Put on the HMD and enjoy!
