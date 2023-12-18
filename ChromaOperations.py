import time
import chromadb
from chromadb.utils import embedding_functions
import Config

client = Config.client

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key="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",
    model_name="text-embedding-ada-002"
)


# def get_client():
#     print(client.__hash__())
#     return client


def create_collection(name: str):
    """
    Create a ChromaDB collection
    :param name: name for the collection
    :return: a collection object
    """
    try:
        collection = client.create_collection(name=name,
                                              embedding_function=openai_ef,
                                              metadata={"hnsw:space": "cosine"})

       # print("\nCollection:", name, "Created\n")
        return collection
    except Exception as ex0:
        return {"error": str(ex0)}    #Returning the error instead of printing
       
       # print("Exception in create_collection():\n" + str(ex0))


def get_collection(name: str):
    """
        Get a ChromaDB collection
        :param name: name for the collection
        :return: a collection object
        """
    try:
        collection = client.get_collection(name=name, embedding_function=openai_ef)
        return collection
    except Exception as ex2:
        print("Exception in get_collection():\n" + str(ex2))


def delete_collection(name: str):
    """
        Delete a ChromaDB collection
        :param name: name for the collection
        :return: None
        """
    try:
        client.delete_collection(name=name)
        print("Collection Deleted\n")
    except Exception as ex2:
        print("Exception in delete_collection():\n" + str(ex2))


def query_collection(input_query: str, num_results: int, collection):
    """
    Queries your collection and return results
    :param input_query: The Input query to search docs
    :param num_results: number of results required
    :param collection: collection to query
    :return: a list of search results of str type
    """
    try:
        chroma_start_time = time.time()
        search_results = collection.query(
            n_results=num_results,
            query_texts=[input_query]
        )
        chroma_end_time = time.time()
        elapsed_time = chroma_end_time - chroma_start_time
        print(f"\nChroma Lookup Time: {elapsed_time:.2f} seconds")
        result = search_results['documents'][0]
        return result
    except Exception as ex3:
        print("Exception in query_collection():\n" + str(ex3))


def list_collections():
    collection_list = client.list_collections()
    if len(collection_list) == 0:
        return []
    else:
        # for i in range(len(collection_list)):
        #     print(f'{i + 1}.', collection_list[i].name)
        return collection_list

def list_docs_in_collection(collection_name):        # Created New Method 
    try:
        collection_list = client.list_collections()
        if collection_name not in [col.name for col in collection_list]:
            return "Collection not found"

        metadata_list = client.get_collection(collection_name).get()['metadatas']
        doc_names = [file_name['file_name'] for file_name in metadata_list]
        return doc_names
    except Exception as e:
        return str(e)

# def list_docs_in_collection(collection):      #Added Collection as an Argument.
#     collection_list = client.list_collections()
#     if len(collection_list) == 0:
#         print("No Collections in DB")
#     else:
#         print('\nSelect a Collection to see documents:\n')
#         for i in range(len(collection_list)):
#             print(f'{i + 1}.', collection_list[i].name)
#         collection_name = input('\nCollection Name: ')
#         # if collection_name in collection_list:
#         metadata_list = client.get_collection(collection_name).get()['metadatas']
#         doc_names = set()

#         for file_name in metadata_list:
#             doc_names.add(file_name['file_name'])
#             # print(doc_name['file_name'])

#         print('\nDocuments in the given Collection are:\n')
#         for i in range(len(doc_names)):
#             print(f'{i + 1}. {doc_names.pop()}')
#         print()

        # else:
        #     print('Invalid Collection Name')
        


if __name__ == "__main__":
	list_collections()
