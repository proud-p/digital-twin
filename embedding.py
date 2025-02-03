import os
from openai import AzureOpenAI
import dotenv
import pandas as pd
from tqdm import tqdm
import numpy as np
import faiss, glob, pickle, os

dotenv.load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_KEY"),
    api_version="2023-12-01-preview"
)


def create_index(filename):

    #########################################################
    # STEP 1. Read text file and store non-empty lines in a DataFrame 
    #########################################################
    df = pd.DataFrame(columns=["text"])  # Initialize an empty DataFrame

    if filename.endswith(".txt") == False:
        file = filename + ".txt"  # Append ".txt" to filename
    
    else:
        file = filename

    with open(file, "r", errors="ignore") as f:
        text = f.read().split("\n")  # Read the file and split into lines

    for line in text:
        if line.strip():  # If line is not empty empty lines
            df = pd.concat([df, pd.DataFrame([{"text": line}])], ignore_index=True)  # Add lines to DataFrame

    BATCH_SIZE = 4
    embeddings = []

    ######################################################
    # STEP 2. Generate embeddings for each line in batches
    ######################################################
    
    for i in tqdm(range(0,len(df), BATCH_SIZE)):
        # print(df["text"].iloc[i:i+BATCH_SIZE])
        batch_text = df["text"].iloc[i:i+BATCH_SIZE].tolist()
        batch_embeddings = get_embedding_batch(batch_text)
        embeddings.extend(batch_embeddings)

    #########################################################
    # STEP 3. Create and save FAISS index 
    #########################################################

    df["embedding"] = embeddings
    embeddings = np.vstack(df["embedding"].values).astype("float32")
    dimensions = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimensions)
    index.add(embeddings)

    faiss.write_index(index,"knowledge/knowledge_text.txt")

    #########################################################
    # STEP 4. Save text data for later retrieval
    #########################################################
    with open("knowledge/knowledge.pkl", "wb") as f:
        pickle.dump(df["text"], f)  # Save original text as a pickle file

        
def get_embedding_batch(text_list):
    #Calls OpenAI's embedding model and returns embeddings
    response = client.embeddings.create(model="text-embedding-ada-002",input=text_list)
    return [data.embedding for data in response.data] # look into every block of data in response. For every block of data, go to data, embedding section and return that


# Run the function to create an index from "knowledge/context.txt"
create_index("knowledge/POOR THINGS.txt")







