// worker is responsible for client-server communication

let sessionId: string;
let wsUrl: string;
let io: WebSocket;

let init = (event: MessageEvent) => {
  sessionId = event.data.sessionId;
  wsUrl = event.data.wsUrl;
  console.log('Worker initialized with session id:', sessionId);
  io = new WebSocket(wsUrl);

  io.onmessage = (event) => {
    let data = JSON.parse(event.data);
    self.postMessage(data);
  };
};

let sendEvent = (event: MessageEvent) => {
  console.log('Sending event:', event.data.handlerId);
  io.send(JSON.stringify({ handlerId: event.data.handlerId }));
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