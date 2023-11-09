use rand::Rng;
use std::collections::HashMap;
use std::io::Write;
use std::sync::Arc;
use std::sync::Mutex;
use std::sync::OnceLock;

static HANDLER: OnceLock<Arc<Mutex<MetricFileHandle>>> = OnceLock::new();

struct MetricFileHandle {
    target: &'static str,
    current: HashMap<&'static str, u64>,
}
impl MetricFileHandle {
    fn add(&mut self, name: &'static str, value: u64) {
        self.current.insert(name, value);
    }
    fn flush(&self) {
        let mut file = std::fs::OpenOptions::new()
            .create(true)
            .truncate(true)
            .write(true)
            .open(&self.target)
            .unwrap();

        let mut iter = self.current.iter().peekable();
        writeln!(&mut file, "{{").unwrap();
        while let Some((name, value)) = iter.next() {
            writeln!(
                &mut file,
                "    \"{name}\": {value}{}",
                if iter.peek().is_some() { "," } else { "" }
            )
            .unwrap()
        }
        writeln!(&mut file, "}}").unwrap();
    }
}

fn init<'a>() -> &'a Arc<Mutex<MetricFileHandle>> {
    HANDLER.get_or_init(|| {
        Arc::new(Mutex::new(MetricFileHandle {
            target: "./metrics",
            current: HashMap::new(),
        }))
    })
}

fn flush() {
    let reference = init();
    reference.lock().unwrap().flush();
}

fn add(name: &'static str, value: u64) {
    let reference = init();
    reference.lock().unwrap().add(name, value);
}

// Upload 1.
#[test]
fn constant() {
    add("constant", 1);

    flush();
}

// Upload a random integer between 0 and 2^8.
#[test]
fn random_one() {
    add("random_one", rand::thread_rng().gen::<u8>() as u64);

    flush();
}

// Upload a random integer between 0 and 2^16.
#[test]
fn random_two() {
    add("random_two", rand::thread_rng().gen::<u16>() as u64);

    flush();
}

// 1/4 of the time doesn't upload metrics.
#[test]
fn inconsistent() {
    if rand::thread_rng().gen::<u8>() > (u8::MAX / 4) {
        add("inconsistent_constant", 2);
        add("inconsistent_random", rand::thread_rng().gen::<u8>() as u64);
    }

    flush();
}

#[test]
fn many() {
    let mut rng = rand::thread_rng();
    add("random_u8_one", rng.gen::<u8>() as u64);
    add("random_u8_two", rng.gen::<u8>() as u64);
    add("random_u8_three", rng.gen::<u8>() as u64);
    add("random_u16_one", rng.gen::<u16>() as u64);
    add("random_u16_two", rng.gen::<u16>() as u64);
    add("random_u16_three", rng.gen::<u16>() as u64);
    add("random_u32_one", rng.gen::<u32>() as u64);
    add("random_u32_two", rng.gen::<u32>() as u64);
    add("random_u32_three", rng.gen::<u32>() as u64);

    add("random_many_one", rng.gen::<u16>() as u64);
    add("random_many_two", rng.gen::<u16>() as u64);
    add("random_many_three", rng.gen::<u16>() as u64);
    add("random_many_four", rng.gen::<u16>() as u64);
    add("random_many_five", rng.gen::<u16>() as u64);
    add("random_many_six", rng.gen::<u16>() as u64);
    add("random_many_seven", rng.gen::<u16>() as u64);

    flush();
}
