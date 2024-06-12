// worker is responsible for client-server communication

let sessionId: string;
let wsUrl: string;
let io: WebSocket;


let configureIO = (wsUrl: string) => {
  io = new WebSocket(wsUrl);

  io.onmessage = (event) => {
    let data = JSON.parse(event.data);
    self.postMessage(data);
  };

  io.onclose = () => {
    console.log('Worker closed connection');
  };
};

let init = (event: MessageEvent) => {
  sessionId = event.data.sessionId;
  wsUrl = event.data.wsUrl;
  console.log('Worker initialized with session id:', sessionId);
  configureIO(wsUrl);
};

let sendEvent = (event: MessageEvent) => {

  let send = () => {
    let data = { sessionId: sessionId, handlerId: event.data.handlerId, value: event.data.value };
    io.send(JSON.stringify(data));
  };

  // if the connection is already OPEN, send the event immediately
  if (io.readyState === io.OPEN) {
    send();
  }

  // wait for the connection to be OPEN before sending the event
  // retry every 100ms
  let interval = setInterval(() => {
    if (io.readyState === io.OPEN) {
      clearInterval(interval);
      send();
    }
  }, 100);
};

self.addEventListener('message', (event) => {
  console.log('Worker received message from client', event.data);
  switch (event.data.type) {
    case 'init':
      init(event);
      break;
    case 'event':
      sendEvent(event);
      break;
  }
});