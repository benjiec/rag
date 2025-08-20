from query_rag import RAGQueryInterface
import anthropic
from dotenv import dotenv_values


envvars = dotenv_values(".env")
anthropic_client = anthropic.Anthropic(api_key=envvars["ANTHROPIC_API_KEY"])


def format_results(results):
    formatted_results = []
    for i, result in enumerate(results, 1):
        formatted_results.append(f"\n--- Result {i} ---")
        formatted_results.append(f"Document: {result['document']}")

        if 'metadata' in result:
            formatted_results.append("Metadata:")
            for key, value in result['metadata'].items():
                if value:
                    formatted_results.append(f"  {key}: {value}")

        if 'distance' in result:
            formatted_results.append(f"Similarity Score: {1 - result['distance']:.4f}")

        formatted_results.append("-" * 40)

    return "\n".join(formatted_results)


def main():
    print("\n" * 5)

    # create RAG query interface
    rag = RAGQueryInterface()

    # collect prompt
    prompt = input("Prompt: ")

    # generate results
    results = rag.search(prompt)

    # parse into an llm prompt
    formatted_results = format_results(results)
    print("\n" * 5)
    llm_prompt = (
            "You are a helpful assistant in a retrieval-augmented generation system. "
            "You will be given some background information (context) and a user’s question. "
            "Use the background information only to improve the quality of your answer. "
            "Do not mention or reference the background information explicitly. "
            "Do not say things like \"according to the context\" or \"based on the provided text\". "
            "Write your answers as if you already know the information. "
            "If the background information does not contain what you need to justify that your answer is correct, "
            "simply state that you do not know the answer. "
            f"Here is the context from Addgene's gRNA database: \n{formatted_results}\n\n\n"
            f"Answer the following prompt: {prompt}"
            )
    print("\n" * 5)
    print(llm_prompt)

    # query Claude Haiku 3
    message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": llm_prompt
                    }
                ]
            )

    print(message.content[0].text)


if __name__ == '__main__':
    main()
