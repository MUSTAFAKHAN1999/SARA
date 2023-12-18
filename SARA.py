import sys
sys.path.append('./CS790-Special-Interest-Project')

from ChromaOperations import (list_collections, create_collection,
                                               delete_collection, list_docs_in_collection)
from chatbot import ask
from Upload import upload_docs


def main():
    try:
        print("\nWelcome to SARA CLI\n")
        print("Available Operations:"
              "\n1. chat"
              "\n2. upload"
              "\n3. list_collections"
              "\n4. create_collection"
              "\n5. delete_collection"
              "\n6. list_documents"
              "\n7. exit or quit\n")

        while True:
            operation = input("Please input operation: ").lower()

            if operation == 'chat':
                ask()
            elif operation == 'upload':
                upload_docs()
            elif operation == 'list_collections':
                list_collections()
            elif operation == 'create_collection':
                create_collection(input("\nEnter the name of the collection to create: ").lower())
            elif operation == 'delete_collection':
                delete_collection(input("\nEnter the name of the collection to delete: ").lower())
            elif operation == 'list_documents':
                list_docs_in_collection()
            elif operation == 'exit' or operation == 'quit':
                print("\nBye\n")
                sys.exit()
            else:
                print("\nPlease Enter a Valid Option\n ")

    except Exception as SaraException:
        print("Exception in Sara.py:", SaraException)


if __name__ == "__main__":
    main()
