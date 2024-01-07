(function () {

    let getToken = () => {
        return document.querySelector('meta[name="schorle-csrf-token"]').getAttribute('content');
    }

    htmx.createWebSocket = (url) => {
        let urlWithPathAndToken = `${url}?token=${getToken()}&path=${window.location.pathname}`;
        return new WebSocket(urlWithPathAndToken, []);
    }


})()