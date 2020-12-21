use crate::crypto::Digest;
use rand::Rng;
use std::convert::TryInto;

pub struct Mempool;

impl Mempool {
    pub async fn get_payload(&self) -> Digest {
        let mut rng = rand::thread_rng();
        [
            rng.gen::<u128>().to_le_bytes(),
            rng.gen::<u128>().to_le_bytes(),
        ]
        .concat()
        .try_into()
        .unwrap()
    }
}
