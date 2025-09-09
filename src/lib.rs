use pyo3::prelude::*;

// Declare the module
mod client;
mod store;
mod visor;

// Re-export the PySocketStore so Python can see it
pub use client::FastClient;
pub use client::HttpResponse;
pub use client::WebSocketConn;
pub use store::PySocketStore;
pub use visor::ProcessSupervisor;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__doc__", "Schorle core module.")?;
    m.add_class::<ProcessSupervisor>()?;
    m.add_class::<PySocketStore>()?;
    m.add_class::<FastClient>()?;
    m.add_class::<HttpResponse>()?;
    m.add_class::<WebSocketConn>()?;
    Ok(())
}
