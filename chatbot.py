import sys
import time
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, \
    SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from ChromaOperations import query_collection, get_collection, list_collections
import Config

def create_agent(print_thinking=False):
    try:
        # LLM
        llm = ChatOpenAI(model_name=Config.GPT_MODEL, temperature=0,
                         openai_api_key=Config.OPENAI_API_KEY,
                         # tiktoken_model_name="gpt-3.5-turbo-16k"
                         )

        # Prompt
        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template
                ("You are a nice chatbot, your name is SARA, having a conversation with a human."),
                SystemMessagePromptTemplate.from_template
                ("if someone asks who you are, you are SARA stands for Smart AI Retrieval Agent"),
                SystemMessagePromptTemplate.from_template
                ("You answer questions to the user with the context provided"),
                SystemMessagePromptTemplate.from_template
                ("If the user asks you behavioural questions like 'Hi', 'Hello', you answer normally"),
                SystemMessagePromptTemplate.from_template
                 ("You do not use your own knowledge, the user provides you context, "
                  "if you cannot find answer in user provided context, you answer "
                  "'I Cannot find an answer in the provided context'"),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )

        memory = ConversationBufferWindowMemory(k=6, memory_key="chat_history", return_messages=True)
        conversation_agent = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=print_thinking,
            memory=memory
        )
        return conversation_agent

    except Exception as ex:
        print(ex)


def print_like_gpt(answer: str):
    for char in answer:
        print(char, end='', flush=True)
        time.sleep(0.015)
    print()


def ask(question, agent, collection_name):
    try:
        # print("\nAvailable Collections:")
        # list_collections()
        # collection_name = input("\nPlease enter a Collection to ask questions from: ").lower()
        # print('The Collection is', collection_name)
        # Create the conversational agent
        chat_agent = agent
        # Print the Welcome Message
        # print('\n' + chat_agent('Who are you?')['text'])

        # while True:
        # user_question = input("\nPlease Enter Your Question: ")
        user_question = question

        # If 'quit' is the input, exit the program
        # if user_question.lower() == 'quit' or user_question.lower() == 'exit':
        #     print("Quitting...")
        #     sys.exit()

        context = query_collection(input_query=user_question,
                                   collection=get_collection(collection_name),
                                   num_results=5)

        prompt = "Answer the questions based on the given context," \
                 "Question:", user_question, "Context:", " ".join(context), \
		 "if you cannot find an answer, reply with " \
        	 "'I Cannot Find the answer in the provided Texts."
                # "Answer:"
                
        # print("Loading Response...", flush=True, end='')
        # start_time = time.time()
        # print("Prompt:\n" + str(prompt))
        print("\nResults From Chroma:" + "\n\n----------\n\n".join(context)+"\n")
        response = chat_agent(str(prompt))
        # response = chat_agent(user_question)
        # print(chat_agent.memory.buffer_as_str)
        # end_time = time.time()
        # elapsed_time = end_time - start_time
        # print('\r' + f"Response Time: {elapsed_time:.2f} seconds\n")
        # print_like_gpt(response['text'])
        # print(response['text'])
        return response['text']

    except Exception as e:
        return(e)


# if __name__ == "__main__":
    # print(ask('hello'))
