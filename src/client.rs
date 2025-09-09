use std::{
    path::PathBuf,
    sync::{
        atomic::{AtomicU8, Ordering},
        Arc, Mutex,
    },
    time::Instant,
};

use anyhow::Context;
use bytes::Bytes;
use futures_util::{SinkExt, StreamExt};
use pyo3::exceptions::PyStopAsyncIteration;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyString, PyTuple};
use reqwest::{
    header::{HeaderMap, HeaderName, HeaderValue},
    Body, Client, ClientBuilder, Method, Response,
};
use reqwest_websocket::{CloseCode, Message as WsMessage, RequestBuilderExt, WebSocket};
use url::Url as UrlCrate;

// ---------- Logging ----------

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
enum LogLevel {
    Off = 0,
    Error = 1,
    Warn = 2,
    Info = 3,
    Debug = 4,
    Trace = 5,
}

impl LogLevel {
    fn from_str(s: &str) -> Option<Self> {
        match s.to_ascii_lowercase().as_str() {
            "off" => Some(Self::Off),
            "error" => Some(Self::Error),
            "warn" | "warning" => Some(Self::Warn),
            "info" => Some(Self::Info),
            "debug" => Some(Self::Debug),
            "trace" => Some(Self::Trace),
            _ => None,
        }
    }
    fn as_str(self) -> &'static str {
        match self {
            Self::Off => "off",
            Self::Error => "error",
            Self::Warn => "warn",
            Self::Info => "info",
            Self::Debug => "debug",
            Self::Trace => "trace",
        }
    }
}

fn env_default_level() -> LogLevel {
    std::env::var("SCHORLE_FC_LOG")
        .ok()
        .and_then(|s| LogLevel::from_str(&s))
        .unwrap_or(LogLevel::Off)
}

#[inline]
fn lvl_enabled(curr: u8, want: LogLevel) -> bool {
    curr >= want as u8
}

#[inline]
fn eprintln_emoji(prefix: &str, msg: &str) {
    // Single place to format logs — easy to redirect later
    eprintln!("{prefix} {msg}");
}

// ---------- Rust-side core client ----------

#[derive(Clone)]
struct CoreClient {
    base_url: UrlCrate,
    client: Client,
    log_level: Arc<AtomicU8>, // shared across clones
    #[cfg(unix)]
    #[allow(dead_code)]
    uds_path: Option<Arc<PathBuf>>,
}

impl CoreClient {
    #[cfg(unix)]
    #[allow(dead_code)]
    fn socket_path(&self) -> Option<&PathBuf> {
        self.uds_path.as_deref()
    }

    fn set_log_level(&self, lvl: LogLevel) {
        self.log_level.store(lvl as u8, Ordering::Relaxed);
    }
    fn get_log_level(&self) -> LogLevel {
        match self.log_level.load(Ordering::Relaxed) {
            1 => LogLevel::Error,
            2 => LogLevel::Warn,
            3 => LogLevel::Info,
            4 => LogLevel::Debug,
            5 => LogLevel::Trace,
            _ => LogLevel::Off,
        }
    }

    fn log(&self, want: LogLevel, emoji_msg: &str) {
        if lvl_enabled(self.log_level.load(Ordering::Relaxed), want) {
            eprintln_emoji("🧭 FastClient", emoji_msg);
        }
    }

    fn new(base_url: &str, socket_path: Option<PathBuf>) -> anyhow::Result<Self> {
        let base_url =
            UrlCrate::parse(base_url).with_context(|| format!("invalid base_url: {base_url}"))?;

        let mut builder = ClientBuilder::new().cookie_store(true).tcp_nodelay(true);

        #[cfg(unix)]
        let (client, uds_arc) = if let Some(path) = socket_path {
            let arc = Arc::new(path.clone());
            builder = builder.unix_socket(path);
            (builder.build()?, Some(arc))
        } else {
            (builder.build()?, None)
        };

        #[cfg(not(unix))]
        let (client, uds_arc) = {
            if socket_path.is_some() {
                anyhow::bail!("UDS is only supported on Unix targets");
            }
            (builder.build()?, None)
        };

        let this = Self {
            base_url,
            client,
            log_level: Arc::new(AtomicU8::new(env_default_level() as u8)),
            #[cfg(unix)]
            uds_path: uds_arc,
        };

        // Log construction
        #[cfg(unix)]
        {
            if let Some(p) = &this.uds_path {
                this.log(LogLevel::Info, &format!("✨ Created (UDS) base={} uds_path={}", this.base_url, p.display()));
            } else {
                this.log(LogLevel::Info, &format!("✨ Created (TCP) base={}", this.base_url));
            }
        }
        #[cfg(not(unix))]
        {
            this.log(LogLevel::Info, &format!("✨ Created (TCP) base={}", this.base_url));
        }

        Ok(this)
    }

    fn build_url(
        &self,
        path: &str,
        query: Option<&[(String, String)]>,
    ) -> anyhow::Result<UrlCrate> {
        let mut url = if path.starts_with("http://") || path.starts_with("https://") {
            UrlCrate::parse(path)?
        } else if path.starts_with('/') {
            self.base_url.join(&path[1..])?
        } else {
            self.base_url.join(path)?
        };

        if let Some(q) = query {
            let mut pairs = url.query_pairs_mut();
            for (k, v) in q {
                pairs.append_pair(k, v);
            }
            drop(pairs);
        }
        self.log(
            LogLevel::Debug,
            &format!("🧩 build_url path='{path}' -> {url}"),
        );
        Ok(url)
    }
}

// ---------- Python-exposed response (with streaming) ----------

#[pyclass]
pub struct HttpResponse {
    #[pyo3(get)]
    status: u16,
    headers: Py<PyDict>,
    resp: Option<Response>,
    // carry log-level for streaming/read logging
    log_level: Arc<AtomicU8>,
}

#[pymethods]
impl HttpResponse {
    /// Return headers as a Python dict[str, str]
    fn headers<'py>(&self, py: Python<'py>) -> &Bound<'py, PyDict> {
        self.headers.bind(py)
    }

    /// Read full body into bytes (useful for non-streaming requests)
    fn read<'py>(&'py mut self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let resp = self.resp.take().ok_or_else(|| {
            pyo3::exceptions::PyRuntimeError::new_err("response already consumed")
        })?;
        let ll = self.log_level.clone();

        pyo3_async_runtimes::tokio::future_into_py_with_locals(
            py,
            pyo3_async_runtimes::tokio::get_current_locals(py)?,
            async move {
                let t0 = Instant::now();
                let bytes = resp.bytes().await.map_err(to_py_err)?;
                let dur = t0.elapsed().as_millis();
                if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Info) {
                    eprintln_emoji("🧭 FastClient", &format!("📦 read {} bytes in {dur}ms", bytes.len()));
                }
                Python::with_gil(|py| Ok(PyBytes::new_bound(py, &bytes).into_py(py)))
            },
        )
    }

    /// Async iterator yielding raw bytes chunks (for streaming)
    ///
    /// Usage in Python:
    /// async for chunk in resp.aiter_bytes():
    ///     ...
    fn aiter_bytes<'py>(&'py mut self, py: Python<'py>) -> PyResult<Bound<'py, PyResponseStream>> {
        let resp = self.resp.take().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("response already consumed")
        })?;

        let stream = resp.bytes_stream();
        let stream_box: BoxStreamType = Box::pin(stream);

        // Wrap in a Python object that implements __aiter__/__anext__
        let py_stream = Py::new(
            py,
            PyResponseStream {
                stream: Arc::new(Mutex::new(Some(stream_box))),
                log_level: self.log_level.clone(),
                started: false,
            },
        )?;

        Ok(py_stream.into_bound(py))
    }
}

// A boxed stream type for convenience
type BoxStreamType = futures_util::stream::BoxStream<'static, reqwest::Result<Bytes>>;

// Internal: a Python async-iter wrapper over a Rust Stream<Item = reqwest::Result<Bytes>>
#[pyclass]
pub struct PyResponseStream {
    // Wrapped in Arc<Mutex<...>> so we can await next without moving it
    stream: Arc<Mutex<Option<BoxStreamType>>>,
    log_level: Arc<AtomicU8>,
    started: bool,
}

#[pymethods]
impl PyResponseStream {
    #[new]
    fn py_new() -> PyResult<Self> {
        Ok(Self {
            stream: Arc::new(Mutex::new(None)),
            log_level: Arc::new(AtomicU8::new(LogLevel::Off as u8)),
            started: false,
        })
    }

    fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    fn __anext__<'py>(&'py mut self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let stream = self.stream.clone();
        let ll = self.log_level.clone();
        let first = !self.started;
        self.started = true;

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            if first && lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                eprintln_emoji("🧭 FastClient", "🚿 stream start");
            }

            // Take ownership of the stream temporarily to avoid holding mutex across await
            let mut stream_opt = {
                let mut guard = stream.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Stream mutex poisoned")
                })?;
                guard.take()
            };

            let stream_ref = stream_opt.as_mut().ok_or_else(|| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Stream already consumed")
            })?;

            let result = stream_ref.next().await;

            // Put the stream back if it's not exhausted
            if matches!(result, Some(Ok(_))) {
                let mut guard = stream.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Stream mutex poisoned")
                })?;
                *guard = stream_opt;
            }

            match result {
                Some(Ok(chunk)) => {
                    if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                        eprintln_emoji("🧭 FastClient", &format!("🧵 chunk {} bytes", chunk.len()));
                    }
                    Python::with_gil(|py| {
                        let py_bytes = PyBytes::new_bound(py, &chunk);
                        Ok(py_bytes.into_py(py))
                    })
                }
                Some(Err(e)) => {
                    if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Error) {
                        eprintln_emoji("🧭 FastClient", &format!("❌ stream error: {e}"));
                    }
                    Err(to_py_err(e))
                }
                None => {
                    if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                        eprintln_emoji("🧭 FastClient", "✅ stream end");
                    }
                    Err(PyStopAsyncIteration::new_err(()))
                }
            }
        })
    }
}

// ---------- Python-exposed WebSocket ----------

#[pyclass]
pub struct WebSocketConn {
    ws: Arc<Mutex<Option<WebSocket>>>,
    log_level: Arc<AtomicU8>,
    closed: Arc<AtomicU8>, // 0 = open, 1 = closed
}

#[pymethods]
impl WebSocketConn {
    fn send_text<'py>(
        &self,
        py: Python<'py>,
        text: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let s = text.str()?.to_cow()?.into_owned();
        let ws_arc = self.ws.clone();
        let ll = self.log_level.clone();
        let closed = self.closed.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            if closed.load(Ordering::Relaxed) != 0 {
                return Err(ws_consumed());
            }

            if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                eprintln_emoji("🧭 FastClient", &format!("💬 WS -> text {} chars", s.len()));
            }

            // Get temporary access to the WebSocket
            let mut ws_opt = {
                let mut guard = ws_arc.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                })?;
                guard.take()
            };

            let ws = ws_opt.as_mut().ok_or_else(ws_consumed)?;
            let result = ws.send(WsMessage::Text(s)).await;

            // Put the WebSocket back unless it's actually closed
            let mut guard = ws_arc.lock().map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
            })?;
            
            match &result {
                Ok(_) => {
                    // Operation succeeded, put WebSocket back
                    *guard = ws_opt;
                }
                Err(e) => {
                    // Check if this is a connection closure error
                    let error_str = format!("{:?}", e);
                    if error_str.contains("ConnectionClosed") || error_str.contains("AlreadyClosed") {
                        // WebSocket is actually closed, mark as closed and don't put back
                        closed.store(1, Ordering::Relaxed);
                    } else {
                        // Temporary error, put WebSocket back for retry
                        *guard = ws_opt;
                    }
                }
            }

            result.map_err(to_py_err)?;
            Python::with_gil(|py| Ok(py.None()))
        })
    }

    fn send_bytes<'py>(
        &self,
        py: Python<'py>,
        data: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let bytes = if let Ok(b) = data.downcast::<PyBytes>() {
            b.as_bytes().to_vec()
        } else {
            data.extract::<Vec<u8>>()?
        };
        let ws_arc = self.ws.clone();
        let ll = self.log_level.clone();
        let closed = self.closed.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            if closed.load(Ordering::Relaxed) != 0 {
                return Err(ws_consumed());
            }

            if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Debug) {
                eprintln_emoji("🧭 FastClient", &format!("💬 WS -> binary {} bytes", bytes.len()));
            }

            // Get temporary access to the WebSocket
            let mut ws_opt = {
                let mut guard = ws_arc.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                })?;
                guard.take()
            };

            let ws = ws_opt.as_mut().ok_or_else(ws_consumed)?;
            let result = ws.send(WsMessage::Binary(bytes.into())).await;

            // Put the WebSocket back unless it's actually closed
            let mut guard = ws_arc.lock().map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
            })?;
            
            match &result {
                Ok(_) => {
                    // Operation succeeded, put WebSocket back
                    *guard = ws_opt;
                }
                Err(e) => {
                    // Check if this is a connection closure error
                    let error_str = format!("{:?}", e);
                    if error_str.contains("ConnectionClosed") || error_str.contains("AlreadyClosed") {
                        // WebSocket is actually closed, mark as closed and don't put back
                        closed.store(1, Ordering::Relaxed);
                    } else {
                        // Temporary error, put WebSocket back for retry
                        *guard = ws_opt;
                    }
                }
            }

            result.map_err(to_py_err)?;
            Python::with_gil(|py| Ok(py.None()))
        })
    }

    /// Receive next message.
    /// Returns a tuple ("text", str) or ("binary", bytes) or None on close.
    fn receive<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let ws_arc = self.ws.clone();
        let ll = self.log_level.clone();
        let closed = self.closed.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            if closed.load(Ordering::Relaxed) != 0 {
                return Python::with_gil(|py| Ok(py.None()));
            }

            // Get temporary access to the WebSocket
            let mut ws_opt = {
                let mut guard = ws_arc.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                })?;
                guard.take()
            };

            let ws = ws_opt.as_mut().ok_or_else(ws_consumed)?;
            let result = ws.next().await;

            // Handle the message and put WebSocket back if still active
            match &result {
                Some(Ok(WsMessage::Close { .. })) | None => {
                    // Connection closed, mark as closed and don't put back
                    closed.store(1, Ordering::Relaxed);
                }
                _ => {
                    // Put the WebSocket back
                    let mut guard = ws_arc.lock().map_err(|_| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                    })?;
                    *guard = ws_opt;
                }
            }

            match result {
                Some(Ok(msg)) => {
                    let out = Python::with_gil(|py| match msg {
                        WsMessage::Text(text) => {
                            if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                                eprintln_emoji("🧭 FastClient", &format!("📡 WS <- text {} chars", text.len()));
                            }
                            let tuple =
                                PyTuple::new_bound(py, &["text".into_py(py), text.into_py(py)]);
                            tuple.into_py(py)
                        }
                        WsMessage::Binary(data) => {
                            if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                                eprintln_emoji("🧭 FastClient", &format!("📡 WS <- binary {} bytes", data.len()));
                            }
                            let bytes = PyBytes::new_bound(py, &data);
                            let tuple =
                                PyTuple::new_bound(py, &["binary".into_py(py), bytes.into_py(py)]);
                            tuple.into_py(py)
                        }
                        WsMessage::Close { .. } => {
                            if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Info) {
                                eprintln_emoji("🧭 FastClient", "👋 WS close frame");
                            }
                            py.None()
                        }
                        _ => {
                            // Ping/Pong auto-handled by reqwest-websocket
                            py.None()
                        }
                    });
                    Ok(out)
                }
                Some(Err(e)) => {
                    if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Error) {
                        eprintln_emoji("🧭 FastClient", &format!("❌ WS error: {e}"));
                    }
                    Err(to_py_err(e))
                }
                None => Python::with_gil(|py| {
                    if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Info) {
                        eprintln_emoji("🧭 FastClient", "👋 WS closed");
                    }
                    Ok(py.None())
                }),
            }
        })
    }

    /// Async iterator support: return self
    fn __aiter__(slf: PyRef<Self>) -> PyRef<Self> {
        slf
    }

    /// Async iterator: yield messages directly (str or bytes), not tuples
    fn __anext__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let ws_arc = self.ws.clone();
        let ll = self.log_level.clone();
        let closed = self.closed.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            if closed.load(Ordering::Relaxed) != 0 {
                return Err(PyStopAsyncIteration::new_err(()));
            }

            // Take ownership of the WebSocket, loop until we have a yieldable message
            let mut ws_opt = {
                let mut guard = ws_arc.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                })?;
                guard.take()
            };

            let ws = ws_opt.as_mut().ok_or_else(|| PyStopAsyncIteration::new_err(()))?;

            loop {
                let result = ws.next().await;

                match result {
                    Some(Ok(WsMessage::Text(text))) => {
                        if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Trace) {
                            eprintln_emoji("🧭 FastClient", &format!("📡 WS <- text {} chars", text.len()));
                        }
                        // Put back before yielding
                        let mut guard = ws_arc.lock().map_err(|_| {
                            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                        })?;
                        *guard = ws_opt;
                        return Python::with_gil(|py| Ok(text.into_py(py)));
                    }
                    Some(Ok(WsMessage::Binary(data))) => {
                        if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Debug) {
                            eprintln_emoji("🧭 FastClient", &format!("📡 WS <- binary {} bytes", data.len()));
                        }
                        let py_bytes = Python::with_gil(|py| PyBytes::new_bound(py, &data).into_py(py));
                        let mut guard = ws_arc.lock().map_err(|_| {
                            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                        })?;
                        *guard = ws_opt;
                        return Ok(py_bytes);
                    }
                    Some(Ok(WsMessage::Close { .. })) | None => {
                        if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Info) {
                            eprintln_emoji("🧭 FastClient", "👋 WS closed");
                        }
                        // Mark closed, don't put back
                        closed.store(1, Ordering::Relaxed);
                        return Err(PyStopAsyncIteration::new_err(()));
                    }
                    Some(Ok(_)) => {
                        // Ping/Pong/Other control frames — skip and keep waiting
                        continue;
                    }
                    Some(Err(e)) => {
                        if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Error) {
                            eprintln_emoji("🧭 FastClient", &format!("❌ WS error: {e}"));
                        }
                        // Put back before returning error so caller could decide next steps
                        let mut guard = ws_arc.lock().map_err(|_| {
                            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                        })?;
                        *guard = ws_opt;
                        return Err(to_py_err(e));
                    }
                }
            }
        })
    }

    fn close<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let ws_arc = self.ws.clone();
        let ll = self.log_level.clone();
        let closed = self.closed.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            // Mark as closed first
            closed.store(1, Ordering::Relaxed);

            let ws_opt = {
                let mut guard = ws_arc.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket mutex poisoned")
                })?;
                guard.take()
            };

            if let Some(ws) = ws_opt {
                if lvl_enabled(ll.load(Ordering::Relaxed), LogLevel::Info) {
                    eprintln_emoji("🧭 FastClient", "👋 WS close()");
                }
                let _ = ws.close(CloseCode::Normal, None).await;
            }
            Python::with_gil(|py| Ok(py.None()))
        })
    }
}

fn ws_consumed() -> PyErr {
    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("WebSocket already consumed/closed")
}

// ---------- Python-exposed FastClient ----------

#[pyclass]
pub struct FastClient {
    core: Arc<CoreClient>,
}

#[pymethods]
impl FastClient {
    #[new]
    #[pyo3(signature = (base_url, socket_path=None))]
    fn new(base_url: &str, socket_path: Option<String>) -> PyResult<Self> {
        let core = CoreClient::new(base_url, socket_path.map(PathBuf::from)).map_err(to_py_err)?;
        Ok(Self {
            core: Arc::new(core),
        })
    }

    /// Set the log level: "off", "error", "warn", "info", "debug", "trace"
    fn set_log_level(&self, level: &str) -> PyResult<()> {
        let lvl = LogLevel::from_str(level).ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "invalid log level: {level}"
            ))
        })?;
        self.core.set_log_level(lvl);
        Ok(())
    }

    /// Get the current log level as a string.
    fn get_log_level(&self) -> String {
        self.core.get_log_level().as_str().to_string()
    }

    /// await client.request(method, path, *, query=None, headers=None, cookies=None, body=None) -> HttpResponse
    #[pyo3(signature = (method, path, *, query=None, headers=None, cookies=None, body=None))]
    fn request<'py>(
        &self,
        py: Python<'py>,
        method: &str,
        path: &str,
        query: Option<Bound<'_, PyDict>>,
        headers: Option<Bound<'_, PyDict>>,
        cookies: Option<Bound<'_, PyDict>>,
        body: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let core = self.core.clone();
        let method = method.to_uppercase();
        let path = path.to_string();

        let query_pairs = py_query_to_pairs(query)?;
        let headers_map = py_headers_to_headermap(headers)?;
        let cookie_list = py_cookies_to_list(cookies)?;

        let body_req = body.map(|b| py_any_to_body(py, b)).transpose()?;

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let url = core
                .build_url(&path, query_pairs.as_deref())
                .map_err(to_py_err)?;
            let method = Method::from_bytes(method.as_bytes()).map_err(to_py_err)?;

            if lvl_enabled(core.log_level.load(Ordering::Relaxed), LogLevel::Info) {
                core.log(
                    LogLevel::Info,
                    &format!("📤 HTTP {} {}", method.as_str(), url),
                );
            }

            let t0 = Instant::now();

            let mut req_builder = core.client.request(method, url);

            // Add headers
            if let Some(headers) = headers_map {
                req_builder = req_builder.headers(headers);
            }

            // Add cookies
            if let Some(cookies) = cookie_list {
                let cookie_header = cookies
                    .iter()
                    .map(|(name, value)| format!("{name}={value}"))
                    .collect::<Vec<_>>()
                    .join("; ");
                req_builder = req_builder.header("cookie", cookie_header);
            }

            // Add body
            if let Some(body) = body_req {
                req_builder = req_builder.body(body);
            }

            let resp = match req_builder.send().await {
                Ok(r) => r,
                Err(e) => {
                    core.log(LogLevel::Error, &format!("❌ HTTP error: {e}"));
                    return Err(to_py_err(e));
                }
            };

            let elapsed = t0.elapsed().as_millis();
            let status = resp.status().as_u16();
            core.log(LogLevel::Info, &format!("📥 HTTP {status} in {elapsed}ms"));

            // Convert headers to Python dict
            let headers_py = Python::with_gil(|py| {
                let d = PyDict::new_bound(py);
                for (name, value) in resp.headers() {
                    if let Ok(value_str) = value.to_str() {
                        let _ = d.set_item(name.as_str(), value_str);
                    }
                }
                d.into()
            });

            Python::with_gil(|py| {
                let obj = Py::new(
                    py,
                    HttpResponse {
                        status,
                        headers: headers_py,
                        resp: Some(resp),
                        log_level: core.log_level.clone(),
                    },
                )?;
                Ok(obj.into_py(py))
            })
        })
    }

    /// Same as request(), but intended when you plan to stream the body.
    #[pyo3(signature = (method, path, *, query=None, headers=None, cookies=None, body=None))]
    fn request_stream<'py>(
        &self,
        py: Python<'py>,
        method: &str,
        path: &str,
        query: Option<Bound<'_, PyDict>>,
        headers: Option<Bound<'_, PyDict>>,
        cookies: Option<Bound<'_, PyDict>>,
        body: Option<Bound<'_, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        // Returns HttpResponse; caller must use resp.aiter_bytes()
        self.request(py, method, path, query, headers, cookies, body)
    }

    /// await client.ws_connect(path, *, headers=None, secure=False) -> WebSocketConn
    #[pyo3(signature = (path, *, headers=None, secure=false))]
    fn ws_connect<'py>(
        &self,
        py: Python<'py>,
        path: &str,
        headers: Option<Bound<'_, PyDict>>,
        secure: bool,
    ) -> PyResult<Bound<'py, PyAny>> {
        let core = self.core.clone();
        let path = path.to_string();
        let headers_map = py_headers_to_headermap(headers)?;

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let mut url = core.build_url(&path, None).map_err(to_py_err)?;

            // Convert http/https to ws/wss
            let scheme = if secure {
                "wss"
            } else if url.scheme() == "https" {
                "wss"
            } else {
                "ws"
            };
            url.set_scheme(scheme).map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>("Invalid URL for WebSocket")
            })?;

            core.log(LogLevel::Info, &format!("🔗 WS connect {}", url));

            let mut req_builder = core.client.get(url);

            // Add headers
            if let Some(headers) = headers_map {
                req_builder = req_builder.headers(headers);
            }

            let resp = match req_builder.upgrade().send().await {
                Ok(r) => r,
                Err(e) => {
                    core.log(LogLevel::Error, &format!("❌ WS upgrade error: {e}"));
                    return Err(to_py_err(e));
                }
            };
            let ws = match resp.into_websocket().await {
                Ok(ws) => ws,
                Err(e) => {
                    core.log(LogLevel::Error, &format!("❌ WS handshake error: {e}"));
                    return Err(to_py_err(e));
                }
            };

            core.log(LogLevel::Info, "✅ WS open");

            Python::with_gil(|py| {
                let obj = Py::new(
                    py,
                    WebSocketConn {
                        ws: Arc::new(Mutex::new(Some(ws))),
                        log_level: core.log_level.clone(),
                        closed: Arc::new(AtomicU8::new(0)), // 0 = open
                    },
                )?;
                Ok(obj.into_py(py))
            })
        })
    }
}

// ---------- Helpers: Python <-> Rust conversions ----------

fn py_query_to_pairs(query: Option<Bound<'_, PyDict>>) -> PyResult<Option<Vec<(String, String)>>> {
    if let Some(d) = query {
        let mut v = Vec::with_capacity(d.len());
        for (k, val) in d {
            let ks: String = k.extract()?;
            let vs: String = val.extract()?;
            v.push((ks, vs));
        }
        Ok(Some(v))
    } else {
        Ok(None)
    }
}

fn py_headers_to_headermap(headers: Option<Bound<'_, PyDict>>) -> PyResult<Option<HeaderMap>> {
    if let Some(d) = headers {
        let mut map = HeaderMap::with_capacity(d.len());
        for (k, v) in d {
            let name: String = k.extract()?;
            let val: String = v.extract()?;
            let hn = HeaderName::from_bytes(name.as_bytes()).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("bad header name: {e}"))
            })?;
            let hv = HeaderValue::from_str(&val).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("bad header value: {e}"))
            })?;
            map.append(hn, hv);
        }
        Ok(Some(map))
    } else {
        Ok(None)
    }
}

fn py_cookies_to_list(
    cookies: Option<Bound<'_, PyDict>>,
) -> PyResult<Option<Vec<(String, String)>>> {
    if let Some(d) = cookies {
        let mut v = Vec::with_capacity(d.len());
        for (k, val) in d {
            let name: String = k.extract()?;
            let value: String = val.extract()?;
            v.push((name, value));
        }
        Ok(Some(v))
    } else {
        Ok(None)
    }
}

fn py_any_to_body(_py: Python<'_>, any: Bound<'_, PyAny>) -> PyResult<Body> {
    if let Ok(b) = any.downcast::<PyBytes>() {
        Ok(Body::from(b.as_bytes().to_vec()))
    } else if let Ok(s) = any.downcast::<PyString>() {
        Ok(Body::from(s.to_cow()?.into_owned()))
    } else {
        // try into Vec<u8>
        let v: Vec<u8> = any.extract()?;
        Ok(Body::from(v))
    }
}

fn to_py_err<E: std::fmt::Display>(e: E) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string())
}
