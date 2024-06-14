# DISTRIBUTION STATEMENT A. Approved for public release. Distribution is unlimited.

# This material is based upon work supported by the Under Secretary of Defense for
# Research and Engineering under Air Force Contract No. FA8702-15-D-0001. Any opinions,
# findings, conclusions or recommendations expressed in this material are those
# of the author(s) and do not necessarily reflect the views of the Under
# Secretary of Defense for Research and Engineering.

# © 2023 Massachusetts Institute of Technology.

# Subject to FAR52.227-11 Patent Rights - Ownership by the contractor (May 2014)

# The software/firmware is provided to you on an As-Is basis

# Delivered to the U.S. Government with Unlimited Rights, as defined in DFARS Part
# 252.227-7013 or 7014 (Feb 2014). Notwithstanding any copyright notice,
# U.S. Government rights in this work are defined by DFARS 252.227-7013 or
# DFARS 252.227-7014 as detailed above. Use of this work other than as specifically
# authorized by the U.S. Government may violate any copyrights that exist in this work.

import Handler
# from ToyStory.HandlingToys import ToyHandling
import argparse, os

print("Starting main script...")

parser = argparse.ArgumentParser()
defaultAddress = os.environ.get("WORKER_ADDRESS", "404")

parser.add_argument("--address", type=str, default=defaultAddress)
parser.add_argument("--altGptAddress", type=str, required=False)
parser.add_argument("--model", type=str, default="Groq")
parser.add_argument("--message", type= str, default="")
# parser.add_argument("--toys", action="store_true")
parser.add_argument("--testing", action="store_true")


url = parser.parse_args().address

if url == "404":
    url = input("provide the address of the worker server")

model = parser.parse_args().model
altGptAddress = parser.parse_args().altGptAddress
# gpt_ask = parser.parse_args().message
# playingWithToys = parser.parse_args().toys

print(f"Connecting to server at {url} with model {model}...")

PATH_TO_CHAT_HISTORY = "chatHistory"

# if not playingWithToys:
platform = Handler(PATH_TO_CHAT_HISTORY, url, model, altGptAddress)

gpt_ask = input("ask llama3 anything you want. Type 'end' to exit shell")
while gpt_ask.lower() != 'end':
    llm_result = platform.chatInputted(gpt_ask)
    gpt_ask = input("ask llama3 anything you want. Type 'end' to exit shell")

print("PRINTING GPT RESULT-----------------", llm_result, len(llm_result))
print("Handler initialized. Disconnecting server handler...")
# def process_input(gpt_ask):
#     llm_result = platform.chatInputted(gpt_ask)
#     return llm_result

# if __name__ == "__main__":
#     input_data = json.loads(sys.stdin.read())
#     gpt_ask = input_data['gpt_ask']
#     llm_result = process_input(gpt_ask)
#     print(json.dumps({"llm_result": llm_result}))
#     platform.serverHandler.disconnect()
#     print("Disconnected.")


platform.serverHandler.disconnect()
print("Disconnected.")
# else:
#     print("toys it is")
    # ToyHandling(PATH_TO_CHAT_HISTORY, url, model, altGptAddress)