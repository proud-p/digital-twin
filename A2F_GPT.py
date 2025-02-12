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

###################################
# STEP 2: Get Similarity Between Prompt and Knowledge Base
###################################

def get_similarity(index, knowledge, prompt, k):
    response = client.embeddings.create(model="text-embedding-ada-002", input=[prompt])
    embedding = response.data[0].embedding

    embedding_array = np.array(embedding).astype("float32")
    embedding_array = embedding_array.reshape(-1, embedding_array.shape[0])

    D, I = index.search(embedding_array, k=k)
    indices = I[0]

    selected = ""
    for i in indices:
        selected += "\n" + knowledge.iloc[i]

    return selected

###################################
# STEP 3: Generate Response from ChatGPT
###################################

def get_response(prompt):
    """Generate a response from ChatGPT based on a given prompt"""
    knowledge_index, knowledge_pkl = load_index(
        "knowledge/knowledge.pkl", "knowledge/knowledge_index.txt"
    )
    context_text = get_similarity(knowledge_index, knowledge_pkl, prompt, 3)
    
    # Constructing the message for the GPT model
    messages = [
        {
            "role": "user",
            "content": f"Imagine you are having a conversation. Answer questions as truthfully as possible getting your response and speaking style from the provided context, and speak conversationally, giving them cues or questions to respond to also. Answer as if you are the person in the provided context, using their writing style, their language, their structure, their tone and any abbreviations \n Context: {context_text} + \n Question: {prompt}",
        },
    ]
    
    # Send the message to GPT-4 model and get the response
    response = client.chat.completions.create(
        model="GPT-4", messages=messages, temperature=0.001  # , stream=True
    )
    answer = response.choices[0].message.content
    
    # Return the generated response
    return answer

###################################
# STEP 4: Main Program Logic
###################################


if __name__ == "__main__":
    
    print("Hi! I am a chatbot.")
    prompt = ""
    
    print("Talk to me")
    
    while True:  # Keep the loop running indefinitely
        prompt = convert_speech_text()  # Get the speech-to-text result
        
        if prompt:  # If speech is recognized
            print(f"YOU: {prompt}")
            
            # Generate a response and proceed
            print(f"ANSWER: {get_response(prompt)}\n")
            answer = get_response(prompt)
            
            ###################################
            # STEP 5: Convert Response to Speech
            ###################################
            get_speech(answer)  # Provide the response in speech form

            ###################################
            # STEP 6: Stream Audio to Omniverse
            ###################################
            # voices audio , prim path (prim path get from omniverse)

            main('voices/audio.wav', '/World/audio2face/PlayerStreaming')
        
        else:
            print("Could not recognize speech. Please try again.")
            continue  # Continue to listen for speech again

            