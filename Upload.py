import os
import sys
import uuid

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader, UnstructuredPowerPointLoader
import Config
from ChromaOperations import get_collection, list_collections
from tqdm import tqdm


def create_chunks(file_list: list):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    chunks = []
    extension = file_list[0].split('.')[-1]
    # if extension.lower() != 'pdf' or extension.lower() != 'pptx':
    #     print('\nInvalid File Format\nOnly .pdf and .pptx are supported\n')
    #     sys.exit()
    # print()
    for file in tqdm(file_list, desc="Creating Chunks"):
        extension = file.split('.')[-1]
        if extension.lower() == 'pdf':
            loader = PyPDFLoader(file)
            pages = loader.load_and_split(text_splitter=text_splitter)
            chunks.append(pages)

        elif extension.lower() == 'pptx':
            loader = UnstructuredPowerPointLoader(file)
            slides = loader.load_and_split(text_splitter=text_splitter)
            chunks.append(slides)
        else:
            print('\n\nFile Not Supported!!!\n')
            sys.exit()
    print("\nChunks Created\n")
    return chunks


def create_vectors(chunk_list: list):
    documents = []
    metadata = []
    ids = []

    for chunks in tqdm(chunk_list, desc="Creating Vectors"):
        id_counter = 0
        for chunk in chunks:
            file_name = os.path.basename(chunk.metadata['source'])
            file_extension = os.path.splitext(chunk.metadata['source'])[1]
            # page_num = chunk.metadata['page']

            documents.append(chunk.page_content)
            metadata.append({
                "file_name": file_name,
                # "page_num": page_num,
                "doc_type": file_extension
            })
            ids.append(file_name + '-' + str(id_counter))
            id_counter = id_counter + 1

    print("\n", len(ids), "Vectors Created\n")
    return documents, metadata, ids


#def upload_to_mysql(file_paths, collection_name):
 #   cursor = Config.connection.cursor()
 #   for file_path in file_paths:
 #       with open(file_path, "rb") as file:
 #           file_data = file.read()
 #       insert_query = "INSERT INTO uploaded_files (file_name, file_content, uuid, collection_name, timestamp) VALUES" \
 #                   " (%s, %s, %s, %s, CURRENT_TIMESTAMP)"
 #       uuid_value = str(uuid.uuid4())
 #       file_name = os.path.basename(file_path)
 #       cursor.execute(insert_query, (file_name, file_data, uuid_value, collection_name))
    
 #   Config.connection.commit()
 #   cursor.close()
 #   Config.connection.close()


def upload_docs(directory_path, collection_name):
    # print("\nAvailable Collections:")
    # list_collections()
    # collection_name = input("\nPlease enter a Collection to upload a document to: ").lower()
    # file_paths = input("\nEnter File Path (pdf and pptx only):")
    # files = [file_paths]
    # files = file_paths.split()
    # files = [path.replace('\\', '/') for path in files]
    # print(files_p)

    file_list = []
    for filename in os.listdir(directory_path):
        if filename.endswith((".pdf", ".pptx")):
            file_path = os.path.join(directory_path, filename)
            file_list.append(file_path)

    chunks = create_chunks(file_list=file_list)
    documents, metadata, ids = create_vectors(chunk_list=chunks)
    print('Collection name is', collection_name)
    collection = get_collection(collection_name)

    batch_size = 50
    for i in tqdm(range(0, len(ids), batch_size), desc="Uploading Vectors to Chroma DB in batches"):
        batch_ids = ids[i:i + batch_size]
        batch_documents = documents[i:i + batch_size]
        batch_metadata = metadata[i:i + batch_size]
        collection.add(documents=batch_documents,
                       metadatas=batch_metadata,
                       ids=batch_ids)
    # upload_to_mysql(file_list, collection_name=collection_name)
    # print("Documents Added")
    # for i in range(len(files)):
    #     print(f"\n{i + 1}.", os.path.basename(files[i]) + "\n")
    
