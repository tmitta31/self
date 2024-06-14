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

import time

from ChatGpt import GroqLlama
from ServerHandler import ServerHandler
from ConversationLedger import ConversationLedger

class Handler():
    """
    This is the main object used by the LLM_Handler application. It is responsible for
    using and managing an array of varrying systems, function, and information.
    """
    def __init__(self, baseDir, url, model, gptAltUrl):
        print("in handler-----------------------")
        """
        PARAMS
            - baseDir is a string that expresses the file path to the chatHistory
                directory.
            - url is a string and the address of the CLEAR worker server.
            - model is a string and expreses which llm to use.
            - gptAltUrl is a string that expresses the address of a web-hosted
                worker server that can query openai servers. This is used if the 
                llm handler is not able to directly communicate with OpenAI.
        """
        print("start intit handler")
        self.givingInstruction = False

        self.BASE_DIR = baseDir
        self.gptAltUrl = gptAltUrl

        # talks to the server, sends info, and gets info from the server
        print("starting servehandler----------------------")
        self.serverHandler = ServerHandler(url, self)
        print("done with server handler-----------------------")

        # Amount of times the conversation has been reset.
        self.conversationCount = 0

        # These two attributes are useful for testing prompt additions added by this script
        # Primarily used for quick testing. But if not testing in this fashion, set this to False
        self.runningTests = False

        self.setLLM(model)
        self.startTime = time.time()
        print("end intit handler")


    # This will set the LLM being used. For example which type of model, gpt vs llama
    def setLLM(self, key, addedInfo = None) :
        """
        Determines and sets which llm to use referencing @key

        PARAMS
            -key is a string that expresses the llm model to use
            -addedInfo defaults to None, but can also be a string that specifies additional
                llm details such as with gpt, determing use of gpt-3 or gpt-4
        """
        print("start setllm handler")

        # If the current model matches the newly set model, we do not create our llm object.
        # Instead we just change parts of the existing object to handle any additional info
        # given.
        if hasattr(self, "lastKeyGiven") and \
            self.lastKeyGiven == key:
                self.languageModel.specifyModel(addedInfo)
                return

        self.lastKeyGiven = key
        LLM_MAP = {
            "Groq": GroqLlama
            }

        # This occurs when app is run with arg for gpt alt url
        if key == "Groq" and self.gptAltUrl is not None: 
            self.languageModel = LLM_MAP[key](altUrl=self.gptAltUrl,
                                               testing = self.runningTests)
        else:
            self.languageModel = LLM_MAP[key](testing = self.runningTests)
        print("end setllm handler")
    
    def givenInstruction(self, sharedJson):
        """
        When a system definition is sent from the coordinator it is processed here.

        PARAMS
            - sharedJson is a dict sent from the coordinator that details CLEAR info,
            such as the robot being used, and also the system definition.
        """
        print("start givenInstructions handler")
        # TODO rename to hardwareType
        self.droneType = sharedJson[0].pop("hardware", None)
        sharedJson = sharedJson[1:]

        # If provided LLM information in given instructions.
        # Currently, this functionality is only being used in testing
        llmInfoGiven = ConversationLedger.filterJson(sharedJson, "llmInfo")
        if llmInfoGiven is not None:
            # If llmInfo is present, it will be at the front
            self.processCommands(llmInfoGiven[0].get("content"))
            sharedJson = sharedJson[1:]

        self.droneType += self.languageModel.modelName

        # need to change coordinator to just send message not json thing
        self.conversationLedger = ConversationLedger(sharedJson[0]["content"], self.BASE_DIR, self.droneType)

        self.chatReady = True
        print("end givenInstructions handler")
    # Processes the input and adjust it for LLM inference
    def chatInputted(self, inputChat, fixedResponse = None, promptToUse = None):
        """
        chatInputted takes in a prompt, and then generates the content which will be
        served to the llm: building a conversation ledger and regenerating a prompt via a RAG
        methodology.

        PARAMS
            - inputChat is a string value that is a prompt sent by the coordinator
            - fixedResponse is a string expressing a fixed version of the previous response
                generated by the LLM. This fixed version is created by the coordinator when the
                response provided is not formatted correctly. In this case, the coordinator infers
                the action selected by the LLM, and then sends its guess back to llm handler.
        """
        print("start chatinputed handler")        
        # Fixing the previous ledger
        self.conversationLedger = ConversationLedger("testing", self.BASE_DIR, "test")
        if fixedResponse is not None:
            self.conversationLedger.updateLastResponse(fixedResponse)
        
        if Handler.checkForCode(inputChat) :
            self.processChat(self.conversationLedger.getFormattedConversation(), code = inputChat)
            return None
        
        self.conversationLedger.addPrompt(inputChat)

        outputChat = self.processChat(self.conversationLedger.getFormattedConversation())

        if outputChat != "conversationReset":
            self.conversationLedger.addResponse(inputChat)
        
        # A string containing LLMs response
        print("end chatInputed handler")
        return outputChat
    
    @staticmethod
    def checkForCode(message) :
        """
        Users on the CLEAR interface may input commands that alter the LLM being used.
        checkForCode just checks if an altering occured in the prompt given.

        PARAMS
            - message is a string and the prompt given by the coordinator
        """
        print("start checkforcode handler")
        flag = "#code"
        if flag in message :
            return True
        return False

    # Either sends the chat to the LLM to get a response, or will
    # detect that a code/command for the system has been given, and will
    # adjust for that.
    def processChat(self, chat, code = None):
        """
        Either sends the chat to the LLM to get a response, or will
        detect that a code/command for the system has been given and will
        adjust for that.

        PARAMS
            - chat is the conversation ledger served as a list of dicts.
            - code defaults to None, but can also be a string expressing LLM settings.
        """
        print("start processchat handler")
        init_time = time.time()

        output = self.processCommands(code) if code else self.queryTheLLM(chat)

        #Means something is broken
        if output == "ERROR":
            # print("generating new path")
            self.startNewConversation()
            output = 'conversationReset'

        timeInferring = (time.time() - init_time)
        print ("time to generate text : {}".format(timeInferring))

        self.outputMessage(output)
        print("end processchat handler-------------", output)
        return output

        
    # Creates a new conversation ledger
    def startNewConversation(self, message = None):
        """
        startNewConversation resets the conversation ledger

        PARAMS
            - due to this function being connected to a socket.io event listener,
            this function can be called with added parameter of message. 
        """
        # The prompts and responses are reset but not the system def.
        # Also reseting the conversation will save the existing
        # conversation ledger in a json file
        print("start conversation handler")
        self.conversationLedger.resetConversation()
        print("end conversation handler")

    #process input for codes or commands
    def queryTheLLM(self, messages):
        """
        queryTheLLM sends the conversation ledger to the LLM, and returns a response.

        PARAMS
            - messages is the conversation ledger as a list of dicts 

        RETURN
            - a string that is the llms response
        """

        # Gives prompt to LLM
        print("start querrythellm handler")
        # return chat_completion.choices[0].message.content
        return self.languageModel.getResponse(messages)
    
    # system message TODO look into
    def processCommands(self, command):
        """
        processCommands facilitates changing llm settings given a command

        PARAMS
            - command is a string indicating a llm setting to change
        RETURN
            - a string that will be proccessed as a llm response
        """
        print("start processcommands handler")
        if "gpt" in command.lower():
            self.setLLM("Groq", command.lower())

        elif "llama" in command.lower():
            self.setLLM("LLaMA2", command.lower())
        
        if hasattr(self, "serverHandler"): 
            self.serverHandler.giveName()
        print("end processcommands handler")
        return "mess(command heard)"
    
    def outputMessage(self, message: str):
        """
        simply outputs the message given. In this case, it will post the
        message to the worker server.
        """
        print("start output message handler")
        self.serverHandler.postResponse(message)
        print("end output message handler")

    
    