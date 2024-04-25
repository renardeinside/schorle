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
  io.send(JSON.stringify(event.data));
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