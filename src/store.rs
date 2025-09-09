use std::{
    net::SocketAddr,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU8, Ordering},
        Arc,
    },
    time::Instant,
};

use anyhow::{Context, Result};
use axum::{
    extract::Path as AxPath,
    http::{HeaderMap, HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    routing::get,
    Router,
};
use axum_server::Handle as AxumHandle;
use dashmap::DashMap;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_async_runtimes::tokio as pyo3_tokio;
use tokio::{fs, sync::Notify, task::JoinHandle};

/// ---------- Logging ----------

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
#[inline]
fn lvl_enabled(curr: u8, want: LogLevel) -> bool {
    curr >= want as u8
}
#[inline]
fn log(prefix: &str, want: LogLevel, curr: u8, msg: impl AsRef<str>) {
    if lvl_enabled(curr, want) {
        eprintln!("{prefix} {}", msg.as_ref());
    }
}
fn env_default_level() -> LogLevel {
    std::env::var("SCHORLE_STORE_LOG")
        .ok()
        .and_then(|s| LogLevel::from_str(&s))
        .unwrap_or(LogLevel::Off)
}

/// ---------- Server mode ----------

#[derive(Clone)]
enum Mode {
    Uds { socket_path: PathBuf },
    Tcp { host: String, port: u16 },
}

#[pyclass(name = "SocketStore")]
pub struct PySocketStore {
    inner: Arc<Inner>,
}

struct Inner {
    mode: Mode,
    // one-shot store; values are removed when fetched
    store: DashMap<String, Vec<u8>>,
    handle: AxumHandle, // TCP graceful shutdown
    server_task: tokio::sync::Mutex<Option<JoinHandle<()>>>,
    running: AtomicBool,
    log_level: AtomicU8,
    uds_shutdown: Notify, // UDS graceful shutdown (persistent; no unsafe swap)
}

#[pymethods]
impl PySocketStore {
    /// Create a new SocketStore.
    ///
    /// Python signature:
    ///   SocketStore(socket_path: str | None = None, host: str | None = None, port: int | None = None)
    #[new]
    #[pyo3(signature = (socket_path=None, host=None, port=None))]
    fn new(socket_path: Option<String>, host: Option<String>, port: Option<u16>) -> PyResult<Self> {
        let mode = if let Some(p) = socket_path {
            Mode::Uds {
                socket_path: PathBuf::from(p),
            }
        } else {
            let host = host.unwrap_or_else(|| "127.0.0.1".to_string());
            let port = port.ok_or_else(|| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    "If socket_path is not set, 'port' must be provided",
                )
            })?;
            Mode::Tcp { host, port }
        };

        let lvl = env_default_level() as u8;
        let this = Self {
            inner: Arc::new(Inner {
                mode: mode.clone(),
                store: DashMap::new(),
                handle: AxumHandle::new(),
                server_task: tokio::sync::Mutex::new(None),
                running: AtomicBool::new(false),
                log_level: AtomicU8::new(lvl),
                uds_shutdown: Notify::new(),
            }),
        };

        match &mode {
            Mode::Tcp { host, port } => {
                log(
                    "🗃️ SocketStore",
                    LogLevel::Info,
                    lvl,
                    format!("✨ Created (TCP) {host}:{port}"),
                );
            }
            Mode::Uds { socket_path } => {
                log(
                    "🗃️ SocketStore",
                    LogLevel::Info,
                    lvl,
                    format!("✨ Created (UDS) {}", socket_path.display()),
                );
            }
        }

        Ok(this)
    }

    /// set(key: str, value: bytes) -> None
    fn set(&self, key: String, value: &[u8]) -> PyResult<()> {
        let lvl = self.inner.log_level.load(Ordering::Relaxed);
        log(
            "🗃️ SocketStore",
            LogLevel::Debug,
            lvl,
            format!("📦 set key='{key}' ({} bytes)", value.len()),
        );
        self.inner.store.insert(key, value.to_vec());
        Ok(())
    }

    fn __aenter__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        self.start(py)
    }

    #[pyo3(signature = (exc_type=None, exc_value=None, traceback=None))]
    fn __aexit__<'py>(
        &self,
        py: Python<'py>,
        exc_type: Option<Bound<'py, PyAny>>,
        exc_value: Option<Bound<'py, PyAny>>,
        traceback: Option<Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        log(
            "🗃️ SocketStore",
            LogLevel::Debug,
            self.inner.log_level.load(Ordering::Relaxed),
            "🧹 exiting the context",
        );
        if let Some(exc_type) = exc_type {
            log(
                "🗃️ SocketStore",
                LogLevel::Debug,
                self.inner.log_level.load(Ordering::Relaxed),
                format!("🧹 exc_type: {exc_type}"),
            );
        }
        if let Some(exc_value) = exc_value {
            log(
                "🗃️ SocketStore",
                LogLevel::Debug,
                self.inner.log_level.load(Ordering::Relaxed),
                format!("🧹 exc_value: {exc_value}"),
            );
        }
        if let Some(traceback) = traceback {
            log(
                "🗃️ SocketStore",
                LogLevel::Debug,
                self.inner.log_level.load(Ordering::Relaxed),
                format!("🧹 traceback: {traceback}"),
            );
        }
        self.stop(py)
    }

    /// start() -> Awaitable[None]
    /// Starts the server (TCP or UDS).
    fn start<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let inner = self.inner.clone();
        pyo3_tokio::future_into_py(
            py,
            async move { inner.start_server().await.map_err(to_py_err) },
        )
    }

    /// stop() -> Awaitable[None]
    /// Stops the server and cleans up (including UDS socket removal).
    fn stop<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let inner = self.inner.clone();
        pyo3_tokio::future_into_py(
            py,
            async move { inner.stop_server().await.map_err(to_py_err) },
        )
    }

    /// get_connection_info() -> dict
    fn get_connection_info(&self, py: Python) -> PyResult<PyObject> {
        let dict = PyDict::new_bound(py);
        match &self.inner.mode {
            Mode::Uds { socket_path } => {
                dict.set_item("mode", "uds")?;
                dict.set_item("socket_path", socket_path.to_string_lossy().to_string())?;
            }
            Mode::Tcp { host, port } => {
                dict.set_item("mode", "tcp")?;
                dict.set_item("host", host)?;
                dict.set_item("port", *port as i64)?;
            }
        }
        Ok(dict.into())
    }

    /// Set log level: "off" | "error" | "warn" | "info" | "debug" | "trace"
    fn set_log_level(&self, level: &str) -> PyResult<()> {
        let lvl = LogLevel::from_str(level).ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("invalid log level: {level}"))
        })?;
        self.inner.log_level.store(lvl as u8, Ordering::Relaxed);
        Ok(())
    }

    /// Get current log level as string
    fn get_log_level(&self) -> String {
        match self.inner.log_level.load(Ordering::Relaxed) {
            1 => LogLevel::Error,
            2 => LogLevel::Warn,
            3 => LogLevel::Info,
            4 => LogLevel::Debug,
            5 => LogLevel::Trace,
            _ => LogLevel::Off,
        }
        .as_str()
        .to_string()
    }
}

impl Drop for Inner {
    fn drop(&mut self) {
        // Best-effort shutdown on drop.
        self.handle.shutdown(); // TCP
        if let Mode::Uds { socket_path } = &self.mode {
            if lvl_enabled(self.log_level.load(Ordering::Relaxed), LogLevel::Debug) {
                eprintln!(
                    "🗃️ SocketStore 🧹 drop() removing {}",
                    socket_path.display()
                );
            }
            let _ = std::fs::remove_file(socket_path);
        }
    }
}

impl Inner {
    async fn start_server(self: &Arc<Self>) -> Result<()> {
        if self.running.swap(true, Ordering::SeqCst) {
            log(
                "🗃️ SocketStore",
                LogLevel::Debug,
                self.log_level.load(Ordering::Relaxed),
                "⏭️ start(): already running",
            );
            return Ok(());
        }

        let app = self.router();

        match &self.mode {
            Mode::Tcp { host, port } => {
                let addr: SocketAddr = format!("{}:{}", host, port)
                    .parse()
                    .with_context(|| format!("Invalid address: {}:{}", host, port))?;
                let handle = self.handle.clone();
                let make_svc = app.into_make_service();

                log(
                    "🗃️ SocketStore",
                    LogLevel::Info,
                    self.log_level.load(Ordering::Relaxed),
                    format!("🔌 starting TCP on {addr}"),
                );

                let task = tokio::spawn({
                    let loglvl = self.log_level.load(Ordering::Relaxed);
                    async move {
                        if let Err(e) = axum_server::bind(addr).handle(handle).serve(make_svc).await
                        {
                            log(
                                "🗃️ SocketStore",
                                LogLevel::Error,
                                loglvl,
                                format!("❌ TCP server error: {e}"),
                            );
                        } else {
                            log(
                                "🗃️ SocketStore",
                                LogLevel::Info,
                                loglvl,
                                "👋 TCP server exited",
                            );
                        }
                    }
                });

                *self.server_task.lock().await = Some(task);
                log(
                    "🗃️ SocketStore",
                    LogLevel::Info,
                    self.log_level.load(Ordering::Relaxed),
                    "✅ TCP listening",
                );
            }

            Mode::Uds { socket_path } => {
                // Prepare filesystem: remove existing file, ensure parent dir exists.
                if Path::new(socket_path).exists() {
                    let _ = fs::remove_file(socket_path).await;
                    log(
                        "🗃️ SocketStore",
                        LogLevel::Debug,
                        self.log_level.load(Ordering::Relaxed),
                        format!("🧹 removed stale socket {}", socket_path.display()),
                    );
                }
                if let Some(parent) = Path::new(socket_path).parent() {
                    if let Err(e) = fs::create_dir_all(parent).await {
                        log(
                            "🗃️ SocketStore",
                            LogLevel::Warn,
                            self.log_level.load(Ordering::Relaxed),
                            format!("⚠️ could not create parent dir {}: {e}", parent.display()),
                        );
                    }
                }

                let socket_path = socket_path.clone();
                let loglvl = self.log_level.load(Ordering::Relaxed);
                let app_for_task = app.clone();
                let self_for_shutdown = self.clone();

                log(
                    "🗃️ SocketStore",
                    LogLevel::Info,
                    loglvl,
                    format!("🔌 starting UDS on {}", socket_path.display()),
                );

                let task = tokio::spawn(async move {
                    #[cfg(unix)]
                    {
                        use tokio::net::UnixListener;
                        let listener = match UnixListener::bind(&socket_path) {
                            Ok(l) => l,
                            Err(e) => {
                                log(
                                    "🗃️ SocketStore",
                                    LogLevel::Error,
                                    loglvl,
                                    format!("❌ Failed to bind Unix socket: {e}"),
                                );
                                return;
                            }
                        };

                        let make_svc = app_for_task.into_make_service();
                        let server =
                            axum::serve(listener, make_svc).with_graceful_shutdown(async move {
                                // wait until stop() signals
                                self_for_shutdown.uds_shutdown.notified().await;
                            });

                        if let Err(e) = server.await {
                            log(
                                "🗃️ SocketStore",
                                LogLevel::Error,
                                loglvl,
                                format!("❌ UDS server error: {e}"),
                            );
                        } else {
                            log(
                                "🗃️ SocketStore",
                                LogLevel::Info,
                                loglvl,
                                "👋 UDS server exited",
                            );
                        }
                    }
                    #[cfg(not(unix))]
                    {
                        log(
                            "🗃️ SocketStore",
                            LogLevel::Error,
                            loglvl,
                            "❌ Unix sockets not supported on this platform",
                        );
                    }

                    let _ = fs::remove_file(&socket_path).await;
                    log(
                        "🗃️ SocketStore",
                        LogLevel::Debug,
                        loglvl,
                        "🧹 UDS socket removed",
                    );
                });

                *self.server_task.lock().await = Some(task);
                log(
                    "🗃️ SocketStore",
                    LogLevel::Info,
                    self.log_level.load(Ordering::Relaxed),
                    "✅ UDS listening",
                );
            }
        }

        Ok(())
    }

    async fn stop_server(self: &Arc<Self>) -> Result<()> {
        if !self.running.swap(false, Ordering::SeqCst) {
            log(
                "🗃️ SocketStore",
                LogLevel::Debug,
                self.log_level.load(Ordering::Relaxed),
                "⏭️ stop(): not running",
            );
            return Ok(());
        }

        log(
            "🗃️ SocketStore",
            LogLevel::Info,
            self.log_level.load(Ordering::Relaxed),
            "🛑 stop() requested",
        );

        // Signal graceful shutdown
        self.handle.shutdown(); // TCP path
        self.uds_shutdown.notify_waiters(); // UDS path

        // Await the task if present
        if let Some(task) = self.server_task.lock().await.take() {
            let _ = task.await;
        }

        // UDS cleanup (best effort)
        if let Mode::Uds { socket_path } = &self.mode {
            if !socket_path.exists() {
                return Ok(());
            } else {
                if let Err(e) = fs::remove_file(socket_path).await {
                    log(
                        "🗃️ SocketStore",
                        LogLevel::Debug,
                        self.log_level.load(Ordering::Relaxed),
                        format!("🧹 UDS cleanup failed: {e}"),
                    );
                } else {
                    log(
                        "🗃️ SocketStore",
                        LogLevel::Debug,
                        self.log_level.load(Ordering::Relaxed),
                        "🧹 UDS cleaned",
                    );
                }
            }
        }

        log(
            "🗃️ SocketStore",
            LogLevel::Info,
            self.log_level.load(Ordering::Relaxed),
            "✅ stopped",
        );
        Ok(())
    }

    fn router(self: &Arc<Self>) -> Router {
        let state = self.clone();
        Router::new().route(
            // Axum 0.8 wildcard syntax:
            "/{*key}",
            get(move |AxPath(key): AxPath<String>| {
                let state = state.clone();
                async move { state.handle_get(key).await }
            }),
        )
    }

    async fn handle_get(self: &Arc<Self>, key: String) -> Response {
        let start = Instant::now();
        let key_norm = key.trim_start_matches('/').to_string();
        let hit = self.store.remove(&key_norm);

        let mut headers = HeaderMap::new();
        headers.insert("Connection", HeaderValue::from_static("close"));

        let resp = if let Some((_, value)) = hit {
            headers.insert(
                "Content-Type",
                HeaderValue::from_static("application/msgpack"),
            );
            headers.insert(
                "Content-Length",
                HeaderValue::from_str(&value.len().to_string()).unwrap(),
            );
            (StatusCode::OK, headers, value).into_response()
        } else {
            headers.insert("Content-Type", HeaderValue::from_static("text/plain"));
            (StatusCode::NOT_FOUND, headers, "Not Found\n").into_response()
        };

        // Log after constructing response to include status & duration
        let dur_ms = start.elapsed().as_millis();
        let status = resp.status().as_u16();
        let lvl = self.log_level.load(Ordering::Relaxed);
        if status == 200 {
            log(
                "🗃️ SocketStore",
                LogLevel::Info,
                lvl,
                format!("🔍 GET '{key_norm}' → 200 in {dur_ms}ms"),
            );
        } else {
            log(
                "🗃️ SocketStore",
                LogLevel::Warn,
                lvl,
                format!("🔍 GET '{key_norm}' → 404 in {dur_ms}ms"),
            );
        }

        resp
    }
}

fn to_py_err(e: anyhow::Error) -> PyErr {
    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("{e:#}"))
}
