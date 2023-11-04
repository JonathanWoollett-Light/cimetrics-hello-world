use std::fs::File;
use std::sync::OnceLock;
use std::io::Write;
use std::sync::Mutex;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering;
use rand::Rng;

fn append_metric(name: &str, value: u64) {
    static FILE: OnceLock<Mutex<File>> = OnceLock::new();
    static FIRST: AtomicBool = AtomicBool::new(true);

    let guard = FILE.get_or_init(|| {
        Mutex::new(std::fs::OpenOptions::new().create(true).truncate(true).write(true).open("./metrics").unwrap())
    });

    // If the 1st value.
    if let Ok(true) = FIRST.compare_exchange(true, false, Ordering::SeqCst, Ordering::SeqCst) {
        guard.lock().unwrap().write_all(format!("\"{name}\": {value}").as_bytes()).unwrap();
    }
    // If not the 1st value.
    else {
        guard.lock().unwrap().write_all(format!(", \"{name}\": {value}").as_bytes()).unwrap();
    }
    
    
}

// Upload 1.
#[test]
fn constant() {
    append_metric("constant",1);
}

// Upload a random integer between 0 and 2^8.
#[test]
fn random_one() {
    append_metric("random_one", rand::thread_rng().gen::<u8>() as u64);
}

// Upload a random integer between 0 and 2^16.
#[test]
fn random_two() {
    append_metric("random_two", rand::thread_rng().gen::<u16>() as u64);
}

// 1/4 of the time doesn't upload metrics.
#[test]
fn inconsistent() {
    if rand::thread_rng().gen::<u8>() as u64 > (u64::MAX / 4) {
        append_metric("inconsistent_constant",2);
        append_metric("inconsistent_random", rand::thread_rng().gen::<u8>() as u64);
    }
}