# from flask import Flask
# import requests, jsonify
from Handler import Handler

# app = Flask(__name__)

PATH_TO_CHAT_HISTORY = "chatHistory"
url = "http:localhost:3001"
# model = parser.parse_args().model
model = "Groq"
altGptAddress = ""

# platform = Handler(PATH_TO_CHAT_HISTORY, url, model, altGptAddress)

# # @app.route('/query_llm', methods=['POST'])
# input = input("Enter llm input")
# def query_llm(input):
#     llm_result = platform.chatInputted(input)
#     return llm_result

# print(query_llm(input))
print("starting handler")
platform = Handler(PATH_TO_CHAT_HISTORY, url, model, altGptAddress)

gpt_ask = input("ask llama3 anything you want. Type 'end' to exit shell")
while gpt_ask.lower() != 'end':
    llm_result = platform.chatInputted(gpt_ask)
    gpt_ask = input("ask llama3 anything you want. Type 'end' to exit shell")