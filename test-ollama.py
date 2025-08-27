import ollama

response = ollama.generate(model='llama3.2', prompt='Why is the sky blue?')
print(response['response'])

response = ollama.generate(model='llama3.2', prompt='What is 1+3?')
print(response['response'])
