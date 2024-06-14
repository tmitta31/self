import os, json
from datetime import datetime, timedelta

class ConversationLedger():
    """
    The ConversationLedger platforms LLM perception of given information and
        account for its prior actions/response. Entries of the conversation ledger
          are conceptually divided into three interdependent categories: prompts,
            responses, and system definitions
    """
    def __init__(self, systemDefinition, baseDir, robotType) -> None:
        """
        PARAMS
            - systemDefinition is a string and is the system definton of the 
                conversation ledger.
            - baseDir is a string that expresses the file path to the chatHistory
                directory. 
            - robotType is a string that expresses the robot being used by CLEAR
        """
        self.SYSTEM_DEF = systemDefinition
        self.prompts = []
        self.responses = []
        self.logPath = ""
        # If the base dir something off
        self.baseDir = baseDir
        self.createChatHistoryDirectory(robotType)

    def addPrompt(self, content):
        """
        adds a string value to prompt list

        PARAM
            content is a string
        """
        self.prompts.append(content)
    
    def addResponse(self, content):
        """
        adds a string value to responses list

        PARAM
            content is a string
        """
        # There should always be a prompt before a response
        if len(self.prompts) > 0:
            self.responses.append(content)
    

    def updateLastResponse(self, newContent):
        """
        The coordinator app processes the llm output. When the llm
        does not provide an output that maps cleanly to an action,
        it makes a sort of guess on what the llm wants. When this occurs,
        the coordinator sends a properly formatted representation of its
        previous reply. This information is relayed to the llm handler in the
        same post request as prompts.

        PARAMS
            newContent is a string value.
        """
        if self.responses: 
            self.responses[-1] = newContent  
        else:
            print("No responses to update.")

    # this gets the system def constant
    def getSystemDefinition(self):
        return self.SYSTEM_DEF

    # Can add sysDef to have dynamic ledger
    def getFormattedConversation(self, sysDef = None):
        """
        PARAMS
            sysDef defaults to None, but can callers can also use it to pass
            a modified system definition. This is useful for LLM handler actions.
        RETURN
            returns a list of dicts that express the system def, prompts and responses
        """
        if sysDef is None: sysDef = self.SYSTEM_DEF

        systemDefFormatted = {"role": "system", "content": sysDef}
        content = [systemDefFormatted]
        
        # Iterate over the length of the longer list (prompts or responses)
        for i in range(max(len(self.prompts), len(self.responses))):
            if i < len(self.prompts): 
                content.append({"role": "user", "content": self.prompts[i]})
            if i < len(self.responses): 
                content.append({"role": "assistant", "content": self.responses[i]})
        return content

    def resetConversation(self):
        """
        saves the current conversation ledger as json file, and then points the prompts
        and responses to new empty lists.
        """
        self.saveConversation()
        self.prompts = []
        self.responses = []
        
    def createChatHistoryDirectory(self, robotType):
        """
        creates the file directory that will store all of our conversation ledgers,
        saved as json files.

        PARAMS
            robotType is a string expressing the name of the robot system being controlled.
                It is used to determine which directory 
        """
        directory = os.path.join(self.baseDir, robotType)

        # This makes a chathistory directory if it did not already exist.
        # If it does exist no exceptions are raised.
        os.makedirs(directory, exist_ok=True)

        now = datetime.now()
        recent_dirs = [d for d in os.listdir(directory) if ( 
                       os.path.isdir(os.path.join(directory, d)) and 
                        now - datetime.strptime(d, "%m-%d-%y_%H-%M") < timedelta(minutes=30))]

        if recent_dirs:
            chatDir = os.path.join(directory, max(recent_dirs, 
                key=lambda d: datetime.strptime(d, "%m-%d-%y_%H-%M")))
        else:
            timestamp = now.strftime("%m-%d-%y_%H-%M")
            chatDir = os.path.join(directory, timestamp)
            os.makedirs(chatDir, exist_ok=True)
        
        # chatDir is a string value expressing the file path to the directory
        # storing our conversation ledgers formatted as jsons.
        self.chatDir = chatDir

    def generateChatFilePath(self):
        """
        Determines and sets the file path for saving the conversation ledger
        as a json.
        """
        INCREMENT_VAL = 1 
        # print(f"\nThe filepath is {self.chatDir}\n")
        files = [f for f in os.listdir(self.chatDir) if (os.path.isfile
                (os.path.join(self.chatDir, f)) and f.startswith("chat"))]
        if not files:
            self.logPath = os.path.join(self.chatDir, "chat-0.json")
        
        # print(files)
        max_index = max([int(f.split('-')[1].split('.')[0]) for f in files if '-' in f], default=0)
        self.logPath = os.path.join(self.chatDir, f"chat-{max_index + INCREMENT_VAL}.json")
    
    def saveConversation(self):
        """
        Saves the conversation ledger as a file @self.logPath
        """
        self.generateChatFilePath()
        with open(self.logPath, "w") as file:
            json.dump(self.getFormattedConversation(), file)
    
    @staticmethod
    def filterJson(dictList, value):
        """
        Takes in a list of dicts and returns all dicts that have the key value
        pair role:@value

        PARAMS
            - dictList is a list of dicts.
            - value is the key value being search for
        """
        arr = [d for d in dictList if d.get("role") == value]
        return arr if arr != [] else None