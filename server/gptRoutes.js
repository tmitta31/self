// DISTRIBUTION STATEMENT A. Approved for public release. Distribution is unlimited.

// This material is based upon work supported by the Under Secretary of Defense for 
// Research and Engineering under Air Force Contract No. FA8702-15-D-0001. Any opinions,
// findings, conclusions or recommendations expressed in this material are those 
// of the author(s) and do not necessarily reflect the views of the Under 
// Secretary of Defense for Research and Engineering.

// © 2023 Massachusetts Institute of Technology.

// Subject to FAR52.227-11 Patent Rights - Ownership by the contractor (May 2014)

// The software/firmware is provided to you on an As-Is basis

// Delivered to the U.S. Government with Unlimited Rights, as defined in DFARS Part 
// 252.227-7013 or 7014 (Feb 2014). Notwithstanding any copyright notice, 
// U.S. Government rights in this work are defined by DFARS 252.227-7013 or 
// DFARS 252.227-7014 as detailed above. Use of this work other than as specifically
// authorized by the U.S. Government may violate any copyrights that exist in this work.

const { Configuration, GroqApi } = require("groq");
const express = require('express');
const router = express.Router();

module.exports = function (io) {
  
  const configuration = new Configuration({
    // Going to have to manually enter this if launch on web
    organization: "YOUR ORGANIZATION Key",
    apiKey: "YOUR GPT API KEY",
  });
  // client = Groq( api_key= configuration.apiKey)
  const groqllama = new GroqApi( api_key= configuration.apiKey);
  let gptOutput = null;
  
  router.post('/chat', async (req, res) => {
    const chatinput = req.body.string;
    const model = req.body.model;

    let generatedChat = null;

    // set a timeout of 10 seconds
    const timeout = new Promise((_, reject) => {
      const id = setTimeout(() => {
        clearTimeout(id);
        reject('Server timed out after 10s');
      }, 10000);
    });

    try {
      generatedChat = await Promise.race([
        groqllama.createChatCompletion({
          "model": model,
          "messages": chatinput,
          "max_tokens": 48
        }),
        timeout
      ]);

      if (generatedChat.data && generatedChat.data.choices && generatedChat.data.choices.length > 0) {
        gptOutput = generatedChat.data.choices[0].message.content;
        io.emit('chat_updated', 'Client is requesting instructions.');
        res.status(200).json({ status: 'success', message: gptOutput});
      } 
      else {
        res.status(500).json({ status: 'error', message: 'Failed to generate chat'});
      }
    } 
    catch (err) {
      console.error(err);
      if(err.toString().includes('Server timed out after 10s')){
        res.status(500).json({ status: 'error', message: 'Server timed out after 10s'});
      } else {
        res.status(500).json({ status: 'error', message: 'Failed to generate chat'});
      }
    }
  });
  
  return router;
};