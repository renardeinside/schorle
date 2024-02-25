
interface ClientMessage {
    trigger: string;
    target: string;
    value: string | null;
}

enum Action {
    morph = 'morph',
}

interface ServerMessage {
    target: string;
    payload: string;
    action: Action;
}

export { ClientMessage, ServerMessage, Action };