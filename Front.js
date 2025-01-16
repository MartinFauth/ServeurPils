const socket = new WebSocket("ws://localhost:8000/ws");

socket.onopen = () => {
    console.log("WebSocket connected");
    socket.send("Hello from React!");
};

socket.onmessage = (event) => {
    console.log("Message from server:", event.data);
};

socket.onclose = () => {
    console.log("WebSocket disconnected");
};
