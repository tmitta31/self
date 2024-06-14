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
import requests, json, time, asyncio, os
from groq import Groq


class GroqLlama():
    ATTEMPT_TOLERANCE = 3

    def __init__(self, canAccessGpt = True, modelInfo = None,
                altUrl = None, testing = False, logPrints = True):
        gptType = modelInfo if modelInfo is not None else "8b"  # set groq llama model info

        self.testing = testing
        self.logPrints = logPrints
        
        self.specifyModel(gptType)
        
        self.gptAltAddress = (os.environ.get("ALT_GPT_URL", None) if altUrl is None
                        else altUrl)
        # self.gptKey = os.environ.get("Groq_API_KEY", None)
        self.gptKey = "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"

        self.canAccessGpt = canAccessGpt
        
        self.timeLastCalled = 0
        self.scriptStartTime = time.time()

        # self.testForGptFirewall()
    
    def specifyModel(self, message):
        """
        PARAMS
            message is a string that will express which model of gpt to run
        """
        if "8b" in message :
            self.modelName = "llama3-8b-8192"
            self.waitingTime = 2

        elif "70b" in message :
            self.modelName = "llama3-70b-8192"
            self.waitingTime = 5
        
        if self.testing:
            self.waitingTime = 15

        # See if there is a proxy test for firewall is just a sample conversation ledger
    # def testForGptFirewall(self):
    #     # Loads a sample conversation ledger and uses it to test for firewall
    #     with open("LLM_handler/platforms/GPT/testForFirewall.json", 'r') as f:
    #         data = json.load(f)

    #     temp = self.modelName
        
    #     # Use gpt-3.5 model for test
    #     self.specifyModel("8b")

    #     if self.gptKey is None:
    #         if self.gptAltAddress is None:
    #             self.gptKey = input("Enter your Groq API Key or enter X if you do not wish to\n")
    #         else:
    #             # If we already have alt address and not gpt key, we assume to use alt address
    #             self.canAccessGpt = False

    #     if self.canAccessGpt:
    #         # openai.api_key = self.gptKey

    #         response = self.getResponse(data) 

    #         if response == "ERROR":
    #             self.canAccessGpt = False
    #             print("Having problems using the python gpt api.\n" \
    #                 + "Swapping to alternative methods.")
                
    #             if self.gptAltAddress is None: 
    #                 self.gptAltAddress = input(
    #                     "Provide an address that can middleman " \
    #                     + "a connection to the gpt api.\n Generally this problem occurs" \
    #                         + "when there exists a firewall preventing access.\n" \
    #                         +"The CLEAR worker server can be webhosted and used to fix this.\n"
    #                     )

    #     self.specifyModel(temp)
    # Where we begin the process of querying the LLM
    def getResponse(self, messages, timesTried = 0):
        """
        PARAMS
            - messages is the conversation ledger, sent as a list of dicts, we are
                sending to the LLM. It is formatted using the specifications of the
                OpenAI models. 
            - timesTried is an int that tracks how many times we have tried querying the LLM.
                getResponse is recursive, and will call itself if failing to get a response from
                model. After @ATTEMPT_TOLERANCE attempts the function will stop tring
        RETURN
            A string expressing the LLMs response, or a string that says ERROR if the query failed
        """
        # We are using a coroutine to prevent stalling. It is common for an error to occur when
        # communicating with the LLM. When these occur, the program run sits untill a response is returned.
        # But our coroutine allows us to implement a timeout, a way to circumvent problematic long response times.
        async def _getResponse(messages = messages, timesTried = timesTried):
            if self.timeLastCalled + self.waitingTime > time.time() :
                await asyncio.sleep((self.timeLastCalled + self.waitingTime) - time.time())
            
            self.timeLastCalled = time.time()

            if timesTried >= 3 : 
                print(f"bummers\n content is \n{messages}")
                return "ERROR"
            try :
                reply = (await self.queryGptApiDirect(messages) if self.canAccessGpt 
                            else self.queryGptIntermediate(messages))
                # print (reply)
                return (reply if reply is not None
                            else await _getResponse(messages, 
                                timesTried=timesTried+1))
            except Exception as e :
                print(e)
                await asyncio.sleep(2)
                return await _getResponse(messages, timesTried=timesTried+1)
        return asyncio.run(_getResponse())
    
    # Handles the asynchronous GPT API calls and exceptions
    async def queryGptApiDirect(self, messages):
        """
        PARAMS
            messages is a list of dictionary objects that represent the conversation ledger
        Return
            either the llms response will be returned, or None if an error occurs.
        """
        try:
            response = await asyncio.wait_for(self.deliverQueryDirect(messages), 
                                              timeout=self.waitingTime * 2)
            # return response["choices"][0]["message"]["content"]
            return response.choices[0].message.content

        except asyncio.TimeoutError:
            print("The Groq API call has timed out.")
            return None

        # except openai.error.InvalidRequestError as e:
        #     print("Exception with GPT: {}".format(str(e)))
        #     return None

        # except openai.error.ServiceUnavailableError as e:
        #     print("Exception with GPT: {}".format(str(e)))
        #     return None

        except Exception as e:
            print("Exception with GPT: {}".format(str(e)))
            return None

    # Helper method to run the synchronous method queryGptDirect asynchronously
    async def deliverQueryDirect(self, messages):
        """
        PARAMS
            messages is a list of dictionary objects that represent the conversation ledger
        Return
            either the llms response will be returned, or None if an error occurs.
        """
        loop = asyncio.get_running_loop()

        def callingGpt(messages):
            client = Groq( api_key= self.gptKey)
            return client.chat.completions.create(
                model=self.modelName,
                messages=messages
            )
        
        return await loop.run_in_executor(None, callingGpt, messages)
    
    # Querying the openai LLM via a web hosted worker server  
    def queryGptIntermediate(self, messages):
        """
        PARAMS
            messages is a list of dictionary objects that represent the conversation ledger
        Return
            either the llms response will be returned, or None if an error occurs.
        """
        url = f"{self.gptAltAddress}/chat"
        response = (requests.post(url,
         json={'string': messages, 'model' : self.modelName},
          timeout = self.waitingTime * 2))
        
        return (GroqLlama.extractMessage(response.content) 
          if response.status_code == 200 else None)

    @staticmethod
    # extractMessage is used for cleaning the content retrieved from the 
    # CLEAR worker server
    def extractMessage(responseContent):
        """
        PARAMS
            responseContent is a dictionary object recieved from the interface server
        Return
            either the llms response will be returned, or None if an error occurs.
        """        
        # Parsing the response content as JSON
        decodedContent = responseContent.decode('utf-8')
        contentJson = json.loads(decodedContent)
        return contentJson.get('message', '')