(function () {

    let getToken = () => {
        return document.querySelector('meta[name="schorle-csrf-token"]').getAttribute('content');
    }

    htmx.createWebSocket = (url) => {
        let urlWithPathAndToken = `${url}?token=${getToken()}&path=${window.location.pathname}`;
        return new WebSocket(urlWithPathAndToken, []);
    }

    let getDevMode = () => {
        return document.querySelector('meta[name="schorle-dev"]').getAttribute('content');
    }

    htmx.logAll();

    htmx.on("htmx:wsBeforeMessage", (evt) => {
        if (getDevMode() === "true") {
            if (evt.detail.message === "reload") {
                // todo - how to make it a soft reload, specifically for the htmx part?
                window.location.reload();
            }
        }
    });

    // TODO: remove this once bug in htmx is fixed
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
        isInlineSwap: function (swapStyle) {
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


})()