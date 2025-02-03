# audio to face gpt

from openai import AzureOpenAI
from csv import writer
from TTS_elevenlabs import get_speech
import os, faiss, pickle, time
import streamlit as st
import numpy as np
import pandas as pd
from STT import convert_speech_text
from pythonosc import udp_client
from audio2face_streaming_utils import main
import dotenv

dotenv.load_dotenv()

# Creates a ChatGPT client based on the key, endpoint and version details given below
client = AzureOpenAI(
    api_key=os.getenv('AZURE_KEY'),
    azure_endpoint=os.getenv('AZURE_ENDPOINT'),
    api_version="2023-12-01-preview",
)

###################################
# STEP 1: Load Index and Knowledge Base
###################################

def load_index(pickle_path, faiss_index_path): 
    # Pickle is a Python library used for serializing and deserializing Python objects.
    # Serialization: Converting a Python object (like a list, dictionary, DataFrame, etc.) into a byte stream.
    # Deserialization: Converting the byte stream back into the original Python object.
    with open(pickle_path, "rb") as f:
        context = pickle.load(f)
    index = faiss.read_index(faiss_index_path)
    return index, context