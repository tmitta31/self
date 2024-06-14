const express = require('express');
const app = express();
const http = require("http");
const {Server} = require('socket.io');
const cors = require("cors");
// const axios = require('axios');

app.use(cors());
const server = http.createServer(app);

const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"],
    },
});

const clientChatRoutes = require('./hostChatRoutes.js');
const gptRoutes = require('./gptRoutes.js');


app.use(express.json(clientChatRoutes(io)));
app.use(gptRoutes(io));

io.on("connection", (socket) => {
    console.log(`User connected: ${socket.id}`)

    socket.on("send_message", async (data) => {
        // const output = await querryLLM(data.message)
        socket.emit("recieve_message", {data})
    });
});

server.listen(3001, () => {
    console.log("Server is running");
});

