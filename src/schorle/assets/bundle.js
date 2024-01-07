(function () {

    let getToken = () => {
        return document.querySelector('meta[name="schorle-csrf-token"]').getAttribute('content');
    }

    htmx.createWebSocket = (url) => {
        let urlWithPathAndToken = `${url}?token=${getToken()}&path=${window.location.pathname}`;
        return new WebSocket(urlWithPathAndToken, []);
    }

    function createMorphConfig(swapStyle) {
        if (swapStyle === 'morph' || swapStyle === 'morph:outerHTML') {
            return {morphStyle: 'outerHTML'}
        } else if (swapStyle === 'morph:innerHTML') {
            return {morphStyle: 'innerHTML'}
        } else if (swapStyle.startsWith("morph:")) {
            return Function("return (" + swapStyle.slice(6) + ")")();
        } else if (swapStyle === "outerHTML") {
            return {morphStyle: 'outerHTML'}
        }
    }

    // TODO: remove this once bug in htmx is fixed
    htmx.defineExtension('morph', {
        isInlineSwap: function(swapStyle) {
            let config = createMorphConfig(swapStyle);
            return config.swapStyle === "outerHTML" || config.swapStyle == null;
        },
        handleSwap: function (swapStyle, target, fragment) {
            let config = createMorphConfig(swapStyle);
            if (config) {
                return Idiomorph.morph(target, fragment.children, config);
            }
        }
    });

    let getDevMode = () => {
        return document.querySelector('meta[name="schorle-dev"]').getAttribute('content');
    }

    switch (getDevMode()) {
        case 'uvicorn_dev':
            console.log(`%cSchorle is running in Uvicorn dev mode.`, `color: #ff9800; font-weight: bold;`);
            let protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            let devWsUrl = `${protocol}://${window.location.host}/_schorle/dev/ws`;
            let devWs = new WebSocket(devWsUrl, []);

            devWs.onopen = () => {
                console.log(`%cSchorle dev websocket connected.`, `color: #ff9800; font-weight: bold;`);
            }

            devWs.onclose = () => {
                console.log(`%cSchorle dev websocket disconnected.`, `color: #ff9800; font-weight: bold;`);
                fetch(window.location.href)
                    .then((response) => {
                        if (response.status === 200) {
                            console.log(`%c server is responding, reloading page`, `color: #ff9800; font-weight: bold;`);
                            window.location.reload();
                        } else {
                            console.log(`%c server is not responding, waiting for updates`, `color: #ff9800; font-weight: bold;`);
                        }
                    })
            }
            break;
        default:
            console.log(`%cSchorle is running in production mode.`, `color: #4caf50; font-weight: bold;`);
    }
})()