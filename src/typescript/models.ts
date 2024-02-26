interface ClientMessage {
  trigger: string;
  target: string;
  value: string | null;
}

enum Action {
  morph = 'morph',
  clear = 'clear',
  render = 'render'
}

interface ServerMessage {
  target: string;
  payload: string;
  action: Action;
  meta?: string;
}

export { ClientMessage, ServerMessage, Action };
