(function () {

    let loadingElementId = "schorle-loading";
    let getToken = () => {
        return document.querySelector('meta[name="schorle-csrf-token"]').getAttribute('content');
    }

    htmx.createWebSocket = (url) => {
        let urlWithPathAndToken = `${url}?token=${getToken()}&path=${window.location.pathname}`;
        return new WebSocket(urlWithPathAndToken, []);
    };

    let getDevMode = () => {
        let devEl = document.querySelector('meta[name="schorle-dev"]');
        return !!devEl;
    }

    // if (getDevMode() === "true") {
    //     htmx.logAll();
    // }


    htmx.on("htmx:wsBeforeMessage", (evt) => {
        if (getDevMode()) {
            if (evt.detail.message === "reload") {
                devReload();
            }
        }
    });

    htmx.on("htmx:wsConfigSend", (evt) => {
        if (evt.detail.triggeringEvent && evt.detail.triggeringEvent.hasOwnProperty("htmx-internal-data")) {
            evt.detail.headers["HX-Trigger-Type"] = evt.detail.triggeringEvent["htmx-internal-data"]["triggerSpec"]["trigger"];
        } else {
            console.log("htmx:wsConfigSend: triggeringEvent not found", evt.detail);
        }
    });

    htmx.on("htmx:load", (evt) => {
        let attributeName = "ws-send";
        let querySelector = "[" + attributeName + "], [data-" + attributeName + "], [data-hx-ws], [hx-ws]";
        // re-trigger processing of nodes with ws-send attribute to ensure that they'll be connected to the websocket
        evt.target.querySelectorAll(querySelector).forEach(function (node) {
            htmx.trigger(node, "htmx:beforeProcessNode");
        })
    });


    htmx.on("htmx:wsClose", (evt) => {
        makeLoadingVisible();
    });

    let makeLoadingVisible = () => {
        if (document.getElementById(loadingElementId)) {
            document.getElementById(loadingElementId).classList.remove("invisible");
        }
    }

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


    let devReload = () => {
        fetch(window.location.href)
            .then((response) => {
                response.text().then((html) => {
                    let parser = new DOMParser();
                    let newDocument = parser.parseFromString(html, "text/html");
                    // appy the theme
                    let currentTheme = document.querySelector('html').getAttribute("data-theme")
                    let newTheme = newDocument.querySelector('html').getAttribute("data-theme")
                    if (currentTheme !== newTheme) {
                        document.querySelector('html').setAttribute('data-theme', newTheme);
                    }
                    // we need to explicitly remove the event handler, otherwise htmx ws will not reinitialize
                    document.getElementById("schorle-event-handler").remove();
                    // first we morph the head to provide new csrf token
                    Idiomorph.morph(document.head, newDocument.head, {morphStyle: "outerHTML"});
                    // then we morph the body to provide new content
                    Idiomorph.morph(document.body, newDocument.body, {morphStyle: "outerHTML"});
                    // finally we need to reinitialize htmx
                    htmx.process(document.body);
                    applyLoadingElement();
                })
            })
    }


    let applyLoadingElement = () => {
        let loadingElement = prepareLoadingElement();
        if (document.getElementById(loadingElementId)) {
            document.getElementById(loadingElementId).remove();
        }
        document.getElementById("schorle-footer").appendChild(loadingElement);
    }

    if (getDevMode()) {
        document.addEventListener("DOMContentLoaded", applyLoadingElement);
    }
    let prepareLoadingElement = () => {
        let element = document.createElement("span");
        element.classList.add("loading", "loading-lg", "text-info", "loading-infinity", "fixed", "right-2", "bottom-2", "invisible");
        element.id = loadingElementId;
        return element;
    }

})()