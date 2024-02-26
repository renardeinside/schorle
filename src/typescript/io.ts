import { ClientMessage } from './models';
import { encode } from '@msgpack/msgpack';

export const sendWhenReady = async (io: WebSocket, message: ClientMessage) => {
  if (io.readyState === WebSocket.OPEN) {
    console.log(`[schorle] Sending message: ${JSON.stringify(message)}`);
    io.send(encode(message));
  } else {
    setTimeout(() => sendWhenReady(io, message), 100);
  }
};
