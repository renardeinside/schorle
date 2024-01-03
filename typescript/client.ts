import htmx from 'htmx.org';

window.onload = () => {
    htmx.logAll();
}

htmx.createWebSocket = (url: string) => {
    console.log(`Received url: ${url}`);
    let urlWithPath = `${url}?path=${window.location.pathname}`;
    console.log("creating websocket with url: " + urlWithPath);
    return new WebSocket(urlWithPath, []);
}