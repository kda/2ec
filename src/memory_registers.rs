use serde::Deserialize;
use std::env;
use std::fs::File;
use std::fs;
use std::io::BufRead;
use std::io::BufReader;
use std::path::Path;
use std::path::PathBuf;

use crate::config;

#[derive(Default, Debug, Deserialize)]
pub struct MemoryRegisters {
    // Not visible externally, just a place to stash the file used for loading
    filename: Option<String>,

    pub location_0: f64,
}

impl MemoryRegisters {
    const DEFAULT_FILENAME: &str = ".2ec.memory_registers.yaml";

    pub fn get_local_filename() -> Option<PathBuf> {
        if let Ok(mut cwd) = env::current_dir() {
            cwd.push(Self::DEFAULT_FILENAME);
            return Some(cwd)
        }
        None
    }

    pub fn get_home_filename() -> Option<PathBuf> {
        if let Some(mut home) = env::home_dir() {
            home.push(Self::DEFAULT_FILENAME);
            return Some(home)
        }
        None
    }


    pub fn load(opt_filename: Option<String>) -> Self {
        let filename = if let Some(passed_filename) = opt_filename {
            // TODO: preserve this name, even if no file currently there, because first time will
            // write it there.
            passed_filename
        } else if let Some(config_filename) = config::Config::find_file() {
            let config_path = Path::new(&config_filename);
            let full_path = fs::canonicalize(config_path).expect("canonicalize failed");
            if let Some(dir) = full_path.parent() {
                dir.join(Self::DEFAULT_FILENAME).to_string_lossy().into_owned()
            } else {
                return Self::default();
            }
        } else {
/* kda_COMMENTED_OUT
            if let Some(config_filename) = config::Config::find_file() {
                default_filename
            } else {
                return Self::default();
            }
  kda_COMMENTED_OUT */
            return Self::default();
        };

        let Ok(file) = File::open(&filename) else {
            //panic!("ERROR: unable to open memory register file {filename}");
            return Self::default();
        };
        let reader = BufReader::new(file);
        let mut instance = Self::parse(reader);
        instance.filename = Some(filename);
        instance
    }

    fn parse<BR: BufRead>(br: BR) -> Self {
        match yaml_serde::from_reader(br) {
            Ok(config) => config,
            e => { panic!("ERROR: unable to parse memory registers {:?}", e); },
        }
    }


    pub fn save(self) {
        let filename = if let Some(filename) = self.filename {
            filename
        } else {
            "".to_string()
        };
    }
}

#[cfg(test)]
mod tests {
    use super::*;
}
