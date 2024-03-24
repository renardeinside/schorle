self.addEventListener('message', (event) => {
  // Extract the origin from the message sent by the main thread
  const origin = new URL(event.data.origin);

  // Determine the WebSocket URL based on the received origin
  const socketUrl = new URL('/_schorle/dev/_events', origin);
  socketUrl.protocol = origin.protocol.startsWith('https') ? 'wss:' : 'ws:';

  // Create a new WebSocket object
  const socket = new WebSocket(socketUrl.toString());

  // Event listener for when the connection is established
  socket.onopen = () => {
    console.log('Connected');
  };

  socket.onmessage = (event) => {
    // empty handler to keep the connection alive
    socket.send('');
  };

  // Event listener for when the connection is closed
  socket.onclose = () => {
    console.log('Connection closed, reloading the window...');
    self.postMessage({ reload: true });
  };
});