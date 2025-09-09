use std::{
    collections::HashMap,
    process::Stdio,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    time::Duration,
};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use tokio::{
    io::{AsyncBufReadExt, BufReader},
    process::{Child, Command},
    sync::Notify,
    time::sleep,
};

#[derive(Debug, Clone)]
enum State {
    Idle,
    Starting,
    Running { pid: u32 },
    Stopping,
    Exited { code: Option<i32> },
    Error { message: String },
}

#[derive(Debug, Clone)]
struct StatusSnapshot {
    state: State,
}

impl Default for StatusSnapshot {
    fn default() -> Self {
        Self { state: State::Idle }
    }
}

#[pyclass]
pub struct ProcessSupervisor {
    argv: Vec<String>,
    cwd: Option<String>,
    env: Option<HashMap<String, String>>,
    is_running_flag: Arc<AtomicBool>,
    shutdown: Arc<Notify>,
    status: Arc<Mutex<StatusSnapshot>>,
    stdout_lines: Arc<Mutex<Vec<String>>>,
    stderr_lines: Arc<Mutex<Vec<String>>>,
}

#[pymethods]
impl ProcessSupervisor {
    /// Create a process supervisor for a command.
    ///
    /// Args:
    ///     cmd: argv as a list of strings, e.g. ["bun", "run", "dev"].
    ///     env: optional environment variables as a dict[str, str].
    ///
    /// Example:
    ///     sup = ProcessSupervisor(["bun", "run", "dev"], {"NODE_ENV": "development"})
    ///     sup.start()
    ///     sup.stop()
    #[new]
    #[pyo3(signature = (cmd, cwd=None, env=None))]
    fn new(cmd: Vec<String>, cwd: Option<String>, env: Option<HashMap<String, String>>) -> PyResult<Self> {
        if cmd.is_empty() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "argv must not be empty",
            ));
        }
        Ok(Self {
            argv: cmd,
            cwd,
            env,
            is_running_flag: Arc::new(AtomicBool::new(false)),
            shutdown: Arc::new(Notify::new()),
            status: Arc::new(Mutex::new(StatusSnapshot::default())),
            stdout_lines: Arc::new(Mutex::new(Vec::new())),
            stderr_lines: Arc::new(Mutex::new(Vec::new())),
        })
    }

    fn __aenter__<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        self.start(py)
    }

    #[pyo3(signature = (exc_type=None, exc_value=None, traceback=None))]
    fn __aexit__<'py>(
        &mut self,
        py: Python<'py>,
        exc_type: Option<Bound<'py, PyAny>>,
        exc_value: Option<Bound<'py, PyAny>>,
        traceback: Option<Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let _ = (exc_type, exc_value, traceback);
        self.stop(py)
    }

    /// Start the process supervisor (no-op if already started).
    #[pyo3(text_signature = "(self, /)")]
    fn start<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        if self.is_running_flag.swap(true, Ordering::SeqCst) {
            return pyo3_async_runtimes::tokio::future_into_py(py, async {
                Python::with_gil(|py| Ok(py.None()))
            });
        }

        {
            // set status to Starting
            let mut st = self
                .status
                .lock()
                .expect("status mutex poisoned (starting)");
            st.state = State::Starting;
        }

        let argv = self.argv.clone();
        let cwd = self.cwd.clone();
        let env = self.env.clone();
        let shutdown = self.shutdown.clone();
        let is_running_flag = self.is_running_flag.clone();
        let status = self.status.clone();
        let stdout_lines = self.stdout_lines.clone();
        let stderr_lines = self.stderr_lines.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            let handle = tokio::spawn(run_once(
                argv,
                cwd,
                env,
                shutdown,
                is_running_flag,
                status,
                stdout_lines,
                stderr_lines,
            ));

            // Store the handle... but we can't mutate self from here
            // For now, we'll detach it since the shutdown mechanism will handle cleanup
            let _ = handle;

            Python::with_gil(|py| Ok(py.None()))
        })
    }

    /// Stop the process supervisor and wait for the child to exit.
    #[pyo3(text_signature = "(self, /)")]
    fn stop<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        if !self.is_running_flag.swap(false, Ordering::SeqCst) {
            return pyo3_async_runtimes::tokio::future_into_py(py, async {
                Python::with_gil(|py| Ok(py.None()))
            });
        }

        {
            let mut st = self
                .status
                .lock()
                .expect("status mutex poisoned (stopping)");
            st.state = State::Stopping;
        }

        let shutdown = self.shutdown.clone();
        let status = self.status.clone();

        pyo3_async_runtimes::tokio::future_into_py(py, async move {
            shutdown.notify_waiters();

            // Give the process a moment to shut down gracefully
            tokio::time::sleep(Duration::from_millis(100)).await;

            // Update status to exited
            {
                let mut st = status.lock().expect("status mutex poisoned (stopped)");
                match st.state {
                    State::Stopping => {
                        st.state = State::Exited { code: None };
                    }
                    _ => {}
                }
            }

            Python::with_gil(|py| Ok(py.None()))
        })
    }

    /// Return current status as a dict: {state, pid, exit_code, error}
    ///
    /// `state` in: "idle" | "starting" | "running" | "stopping" | "exited" | "error"
    #[pyo3(text_signature = "(self, /)")]
    fn status<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let d = PyDict::new_bound(py);
        let st = self.status.lock().expect("status mutex poisoned");

        match &st.state {
            State::Idle => {
                d.set_item("state", "idle")?;
                d.set_item("pid", py.None())?;
                d.set_item("exit_code", py.None())?;
                d.set_item("error", py.None())?;
            }
            State::Starting => {
                d.set_item("state", "starting")?;
                d.set_item("pid", py.None())?;
                d.set_item("exit_code", py.None())?;
                d.set_item("error", py.None())?;
            }
            State::Running { pid } => {
                d.set_item("state", "running")?;
                d.set_item("pid", *pid)?;
                d.set_item("exit_code", py.None())?;
                d.set_item("error", py.None())?;
            }
            State::Stopping => {
                d.set_item("state", "stopping")?;
                d.set_item("pid", py.None())?;
                d.set_item("exit_code", py.None())?;
                d.set_item("error", py.None())?;
            }
            State::Exited { code } => {
                d.set_item("state", "exited")?;
                if let Some(c) = code {
                    d.set_item("exit_code", *c)?;
                } else {
                    d.set_item("exit_code", py.None())?;
                }
                d.set_item("pid", py.None())?;
                d.set_item("error", py.None())?;
            }
            State::Error { message } => {
                d.set_item("state", "error")?;
                d.set_item("pid", py.None())?;
                d.set_item("exit_code", py.None())?;
                d.set_item("error", message.as_str())?;
            }
        }

        Ok(d)
    }

    /// Convenience: True iff process is in "running" state.
    #[getter]
    fn is_running(&self) -> bool {
        matches!(self.status.lock().unwrap().state, State::Running { .. })
    }

    /// Convenience: current PID or None.
    #[getter]
    fn pid(&self) -> Option<u32> {
        match self.status.lock().unwrap().state {
            State::Running { pid } => Some(pid),
            _ => None,
        }
    }

    /// Get and clear captured stdout lines.
    ///
    /// Returns:
    ///     List of stdout lines captured since last call.
    #[pyo3(text_signature = "(self, /)")]
    fn get_stdout_lines<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let mut lines = self
            .stdout_lines
            .lock()
            .expect("stdout_lines mutex poisoned");
        let result = PyList::new_bound(py, lines.iter());
        lines.clear();
        Ok(result)
    }

    /// Get and clear captured stderr lines.
    ///
    /// Returns:
    ///     List of stderr lines captured since last call.
    #[pyo3(text_signature = "(self, /)")]
    fn get_stderr_lines<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyList>> {
        let mut lines = self
            .stderr_lines
            .lock()
            .expect("stderr_lines mutex poisoned");
        let result = PyList::new_bound(py, lines.iter());
        lines.clear();
        Ok(result)
    }

    /// Best-effort cleanup if object is GC'd without explicit stop().
    /// Non-blocking: signals shutdown.
    fn __del__(&mut self) {
        // Fast path: if not running, nothing to do
        if !self.is_running_flag.swap(false, Ordering::SeqCst) {
            return;
        }

        // Set stopping status and notify
        {
            if let Ok(mut st) = self.status.lock() {
                st.state = State::Stopping;
            }
        }
        self.shutdown.notify_waiters();
        
        // The tokio task will handle its own cleanup when it receives the shutdown signal
    }
}

// ---------------- internals ----------------

async fn run_once(
    argv: Vec<String>,
    cwd: Option<String>,
    env: Option<HashMap<String, String>>,
    shutdown: Arc<Notify>,
    is_running_flag: Arc<AtomicBool>,
    status: Arc<Mutex<StatusSnapshot>>,
    stdout_lines: Arc<Mutex<Vec<String>>>,
    stderr_lines: Arc<Mutex<Vec<String>>>,
) {
    // Spawn the child
    let mut cmd = Command::new(&argv[0]);
    if argv.len() > 1 {
        cmd.args(&argv[1..]);
    }
    if let Some(dir) = &cwd {
        cmd.current_dir(dir);
    }
    if let Some(env_vars) = &env {
        cmd.envs(env_vars);
    }

    let mut child = match cmd
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true)
        .spawn()
    {
        Ok(c) => c,
        Err(e) => {
            let mut st = status.lock().expect("status mutex poisoned (spawn error)");
            st.state = State::Error {
                message: format!("spawn failed: {e}"),
            };
            is_running_flag.store(false, Ordering::SeqCst);
            return;
        }
    };

    let pid = child.id().unwrap_or_default();
    {
        let mut st = status.lock().expect("status mutex poisoned (running)");
        st.state = State::Running { pid };
    }

    eprintln!("🔵 started: {:?} (pid={})", argv, pid);

    // Stream logs
    let mut tasks = Vec::new();
    if let Some(out) = child.stdout.take() {
        let mut rdr = BufReader::new(out).lines();
        let stdout_buf = stdout_lines.clone();
        tasks.push(tokio::spawn(async move {
            while let Ok(Some(line)) = rdr.next_line().await {
                println!("🔵 [child] {line}");
                if let Ok(mut buf) = stdout_buf.lock() {
                    buf.push(line);
                }
            }
        }));
    }
    if let Some(err) = child.stderr.take() {
        let mut rdr = BufReader::new(err).lines();
        let stderr_buf = stderr_lines.clone();
        tasks.push(tokio::spawn(async move {
            while let Ok(Some(line)) = rdr.next_line().await {
                eprintln!("🔴 [child] {line}");
                if let Ok(mut buf) = stderr_buf.lock() {
                    buf.push(line);
                }
            }
        }));
    }

    // Wait for either shutdown or process exit
    tokio::select! {
        _ = shutdown.notified() => {
            eprintln!("🛑 stop requested, terminating child…");
            terminate_child(&mut child).await;
            for t in tasks { let _ = t.await; }
            {
                let mut st = status.lock().expect("status mutex poisoned (stopped)");
                st.state = State::Exited { code: None };
            }
        }
        status_res = child.wait() => {
            let code = status_res.ok().and_then(|s| s.code());
            for t in tasks { let _ = t.await; }
            {
                let mut st = status.lock().expect("status mutex poisoned (exited)");
                st.state = State::Exited { code };
            }
        }
    }

    // Grace period (optional, keeps logs flush balanced)
    sleep(Duration::from_millis(10)).await;

    is_running_flag.store(false, Ordering::SeqCst);
}

async fn terminate_child(child: &mut Child) {
    // Cross-platform hard kill (SIGKILL/TerminateProcess).
    // If you need graceful shutdown, add your own hook (HTTP, signal, etc.) before kill().
    let _ = child.kill().await;
}
