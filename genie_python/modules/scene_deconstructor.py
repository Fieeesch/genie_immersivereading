from datetime import datetime
import re
import json
from pathlib import Path
from openai import OpenAI
import config

class SceneSplitterGPT:
    def __init__(self, chunksize: int = config.CHUNKSIZE):

        if config.USE_OPENAI_API:
            print("Using OpenAI GPT model for scene splitting.")
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.model = config.OPENAI_MODEL
        else:
            print("Using local ollama gpt model for scene splitting.")
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",  # Local Ollama API
                api_key="ollama"                       # Dummy key
            )
            self.model = "gpt-oss:20b"

        self.SYSTEM_PROMPT = """
            You are a tool that splits narrative book text into distinct chunks, each chunk representing a different location. 
            Given an input text, you will identify after which paragraphs a location change occurs and respond with the indices of these paragraphs, starting with zero. 
            Put the index numbers into an array of integers. Respond ONLY with this array. If no location changes occur, respond with an empty array.
        """

        self.CHUNKSIZE = chunksize

    def split_book(self, filepath: str) -> list[str]:
        '''
        Reads a book from a given path and lets GPT split it into scenes, each scene representing a sistinct location
        
        :param filepath: filepath of the book text
        :type filepath: str
        :return: the book split into scenes
        :rtype: list[str]
        '''
        splitted_chunks = []

        for c in self._chunk_book(filepath, self.CHUNKSIZE):
            split_indices = self._call_openai(c)
            splitted_chunk = self._split_with_indices(c, split_indices)
            splitted_chunks.append(splitted_chunk)
        
        splitted_book = self._merge_chunk_groups(splitted_chunks)

        return splitted_book
    
    def _chunk_book(self, filepath: str, chunksize: int) -> list[str]:
        '''
        Reads a file and returns text chunks as a list of strings
        
        :param filepath: path of the file
        :type filepath: str
        :param chunksize: number of characters per chunk
        :type chunksize: int
        :return: text chunks
        :rtype: list[str]
        '''
        text = Path(filepath).read_text(encoding="utf-8")
        return [text[i:i + chunksize] for i in range(0, len(text), chunksize)]

    def _call_openai(self, text_chunk: str) -> list[int]:
        '''
        Calls GPT model to return indices of paragraphs with location changes
        
        :param text_chunk: text chunks to analyze
        :type text_chunk: str
        :return: Indices of paragraphs after which a location change occurs, starting with zero
        :rtype: list[int]
        '''
        payload = dict(           
            model = self.model,
            messages = [
                {
                    "role": "system", 
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": text_chunk
                }
            ]
        )

        response = self.client.chat.completions.create(**payload)

        raw = response.choices[0].message.content
        return self._extract_int_list(raw)
    
    def _extract_int_list(self, text: str) -> list[int]:
        '''
        Extracts the first list of integers from a model output.
        Accepts surrounding text and ignores everything except the first found array like [1,2,3].
        '''

        print(text)
        
        pattern = r"\[\s*-?\d+(?:\s*,\s*-?\d+)*\s*\]"
        match = re.search(pattern, text)

        if not match:
            raise ValueError(f"No integer list found in model output: {text!r}")

        array_text = match.group(0)

        try:
            items = [int(x) for x in array_text.strip("[]").split(",")]
        except Exception as e:
            raise ValueError(f"Could not parse integer list from {array_text!r}: {e}")

        return items

    def _split_with_indices(self, text_chunk: str, indices: list[int]) -> list[str]:
        '''
        Splits text into segments.
        
        :param self: Description
        :param text_chunk: Description
        :type text_chunk: str
        :param indices: Description
        :type indices: list[int]
        :return: Description
        :rtype: list[str]
        '''
        # Absätze extrahieren: ein oder mehrere \n\n trennen Paragraphen
        paragraphs = re.split(r'\n\s*\n', text_chunk)

        result = []
        current = []

        for i, para in enumerate(paragraphs):
            current.append(para)

            # Wenn der Absatzindex in indices ist → cut
            if i in indices:
                result.append("\n\n".join(current))
                current = []

        # Rest anhängen, wenn noch Text übrig ist
        if current:
            result.append("\n\n".join(current))

        return result
    
    def _merge_chunk_groups(self, splitted_chunks: list[list[str]]) -> list[str]:
        
        if not splitted_chunks:
            return []

        # Start mit erstem Unterarray
        result = splitted_chunks[0].copy()

        for chunk in splitted_chunks[1:]:
            if not chunk:
                continue

            # Letzten Eintrag des bisherigen result mit dem ersten des neuen Arrays verbinden
            result[-1] = result[-1] + chunk[0]

            # Rest normal anhängen (ab index 1)
            result.extend(chunk[1:])

        return result

class PromptGeneratorGPT:
    def __init__(self):

        if config.USE_OPENAI_API:
            print("Using OpenAI GPT model for prompt generation.")
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.model = config.OPENAI_MODEL
        else:
            print("Using local ollama gpt model for prompt generation.")
            self.client = OpenAI(
                base_url="http://localhost:11434/v1",  # Local Ollama API
                api_key="ollama"                       # Dummy key
            )
            self.model = "gpt-oss:20b"

        self.SYSTEM_PROMPT = """
            You are a tool that generates Prompts for a 360° panorama image generator.
            The input given to you is a part of a narrative text that takes place in one location. Extract details about the location from the text and use them to formulate a short, simple image prompt (under 50 words).
            If the location is surreal or abstract, describe it as accurately as possible. 
            Do not include people, characters or too specific details, as this will confuse the image generator. Respond with ONLY the image prompt. Always respond ONLY in English, regardless of the input language.
        """

    def generate_prompts(self, scenes: list[str]) -> list[str]:
        '''
        Generates image prompts based on book scenes with help of an LLM
        
        :param scenes: Scenes that should be turned into image prompts
        :type scenes: list[str]
        :return: Image Prompt for each input scene
        :rtype: list[str]
        '''

        return [self._call_openai(scene) for scene in scenes]

    def _call_openai(self, scene_text: str) -> str:
        '''
        Calls GPT model to return image prompts for a given scene
        
        :param scene_text: Original book text of the scene
        :type scene_text: str
        :return: image prompt for the scene
        :rtype: str
        '''
        response = self.client.chat.completions.create(
            model = self.model,
            messages = [
                {
                    "role": "system", 
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": scene_text
                }
            ]
        )

        return response.choices[0].message.content