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

import socketio, requests, threading

# Handles the communication between the LLM_handler and the server we are connected to
class ServerHandler():
    def __init__(self, url, system):
        print(f"Connecting to server at {url}...")
        self.sio = socketio.Client()
        self.URL = url        
        self.system = system

        self.givingInstruction = False
        self.chatReady = False

        serverThread = threading.Thread(target=self.startListen)
        self.sio.on("instruction_updated")(self.givenInstruction)
        self.sio.on("host_chat_updated")(self.chatInputted)
        self.sio.on("chat_reset_requested")(self.system.startNewConversation)
        self.sio.on("model_name_requested")(self.giveName)
        self.sio.on("readiness_requested")(self.giveReady)
        serverThread.start()

    def givenInstruction(self, message): 
        """
        givenInstruction is called when a 'instruction_updated' event occurs.
        givenInstruction will perform a get request, retrieving a dictionary
        containing CLEAR system information such as what robot is being used, 
        and the corresponding system definition
        """
        print("Received instruction updated event.")
        if self.givingInstruction: return 
        url = f'{self.URL}/instruction'
        print ("Instruction given to me!")

        response = requests.get(url)
        if response.status_code == 200:
            sharedJson = response.json()
            
            # If sending nothing
            if sharedJson is None:
                return

            self.system.givenInstruction(sharedJson)
            self.chatReady = True
        else:
            print("Error:", response.status_code, response.text)

    def startListen(self):
        """
        Creates an event listener bound to a socket 
        """
        try:
            print("Starting server listener...")
            print ("The URL being used : {}".format(self.URL))
            self.sio.connect(self.URL)
            self.sio.wait()
        except Exception as e:
            print(f"Exception occurred while connecting to server: {e}")
        print("Listener started.")

    def disconnect(self):
        """
        stops event listener, closing the socket
        """
        self.sio.disconnect()

    def giveReady(self, message) :
        """
        triggered by event where other CLEAR applications are checking
        the readiness of other CLEAR apps. This method will post that
        the LLM handler is ready. 
        """
        url = '{}/readyInfo'.format(self.URL)
        requests.post(url,json={"llm_chat":"llm_chat"})

    def chatInputted(self, message):
        """
        triggered by an event where the coordinator posts a prompt, and
        the coordinators interpretation of the LLMs last response
        """
        print("Received host chat updated event.")
        if not self.chatReady :
            return
        
        url = '{}/hostChatInfo'.format(self.URL)
        response = requests.get(url)
        print("chat inputted {}".format(response))

        if (response.status_code == 200) :
            # The current prompt or query
            inputChat = response.json().get('prompt', None)
            # Value to replace previous reponse from the LLM handler
            fixedResponse = response.json().get('fixResponse', None)

            self.system.chatInputted(inputChat, fixedResponse)

        else:
            print("Error:", response.status_code, response.text)

    # Posts the LLM_Handler created content back to the sender
    def postResponse(self, content):
        """
        postResponse posts the llms response, providing the coordinator information 
        to act upon.

        PARAMS
            - content is a string and the llms response
        """
        print(f"Posting response: {content}")
        url = '{}/clientChatInfo'.format(self.URL)
        response = requests.post(url, json={'response': content})
        print ("output is {}".format(content))
        print(f"Response posted: {response}")
        return response
    
    def giveName(self, message=None) :
        """
        Tells the coordinator what langauage model is being used. This is useful if the system definition
        should be changed per model used. Like if using gpt-4 vs llama-13B, the sys def might be dif
        to accomodate the strenghts or weaknesses of the models
        """
        print("my name is, ", self.system.languageModel.modelName)
        url = '{}/llmModel'.format(self.URL)
        response = requests.post(url, json={'model': self.system.languageModel.modelName})
        print("model name requested : ", response)