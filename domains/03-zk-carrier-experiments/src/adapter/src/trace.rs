//! Experimental fusion relation. Explicit hash assumptions and PQ proof qualification remain open.
use anyhow::{Result,ensure};
use binius_circuits::{keccak::permutation::{keccak_f1600,ref_keccak_f1600}};
use binius_core::word::Word;
use binius_frontend::{Circuit,CircuitBuilder,Wire};
use serde_json::Value;
use std::{array,fs,path::Path};

pub const SEATS:usize=64;
pub struct Config {pub fingerprint:Vec<u8>,pub domain:Vec<u8>,pub context:Vec<u8>,keys:[Vec<Vec<u8>>;2]}
pub struct Wires {pub seats:Vec<Wire>,pub seeds:Vec<[Vec<Wire>;2]>,pub public:Vec<Wire>}
pub fn unhex(s:&str)->Result<Vec<u8>> {ensure!(s.len().is_multiple_of(2),"odd hex");(0..s.len()).step_by(2).map(|i|Ok(u8::from_str_radix(&s[i..i+2],16)?)).collect()}
pub fn words(b:&[u8])->Vec<Word>{assert!(b.len().is_multiple_of(8));b.chunks_exact(8).map(|x|Word(u64::from_le_bytes(x.try_into().unwrap()))).collect()}
fn lp(parts:&[&[u8]])->Vec<u8>{parts.iter().flat_map(|p|(p.len()as u64).to_be_bytes().into_iter().chain(p.iter().copied())).collect()}
pub fn shake(data:&[u8],length:usize)->Vec<u8>{
    let mut data=data.to_vec();data.push(0x1f);while !data.len().is_multiple_of(136){data.push(0);}*data.last_mut().unwrap()^=0x80;
    let mut state=[0u64;25];for block in data.chunks_exact(136){for(i,w)in words(block).iter().enumerate(){state[i]^=w.0;}ref_keccak_f1600(&mut state);}
    let mut result=Vec::new();loop{for x in &state[..17]{result.extend_from_slice(&x.to_le_bytes());}if result.len()>=length{result.truncate(length);return result;}ref_keccak_f1600(&mut state);}
}
fn keys(v:&Value,name:&str)->Result<Vec<Vec<u8>>>{
    let a=v[name].as_array().ok_or_else(||anyhow::anyhow!("keys missing"))?;ensure!(a.len()==SEATS,"registry size");
    let k:Vec<Vec<u8>>=a.iter().map(|x|{let b=unhex(x.as_str().ok_or_else(||anyhow::anyhow!("key not hex"))?)?;ensure!(b.len()==64,"key size");Ok(b)}).collect::<Result<_>>()?;
    let mut uniq=k.clone();uniq.sort();uniq.dedup();ensure!(uniq.len()==SEATS,"registry duplicates");Ok(k)
}
impl Config {
    pub fn read(p:&Path)->Result<Self>{
        ensure!(fs::metadata(p)?.len()<=128*1024,"configuration byte limit");
        let v:Value=serde_json::from_slice(&fs::read(p)?)?;
        ensure!(v["seats"]==64&&v["threshold"]==43&&v["seed_bytes"]==48&&v["hash_bytes"]==64&&v["field_polynomial_tail"]==293,"exact fusion parameters");
        let fingerprint=unhex(v["configuration"].as_str().ok_or_else(||anyhow::anyhow!("configuration missing"))?)?;
        let domain=unhex(v["domain"].as_str().ok_or_else(||anyhow::anyhow!("domain missing"))?)?;ensure!(fingerprint.len()==64&&domain.len()==64,"context width");
        ensure!(v["relation"]=="CEQS12B_FIXED_CONTEXT"&&v["pair_bytes"]==128,"exact paired trace suite");
        let ks=[keys(&v,"trace_public_keys")?,keys(&v,"vote_public_keys")?];
        let metadata=b"FIXED-CONTEXT-PAIR/DIRECT-CHALLENGE/GF512/64/43/2x48/v1.27b";
        let mut parts=vec![b"CEQS12B/config".to_vec(),metadata.to_vec()];
        for k in &ks{parts.extend(k.clone());}
        let refs:Vec<&[u8]>=parts.iter().map(Vec::as_slice).collect();
        let derived=shake(&lp(&refs),64);
        ensure!(derived==fingerprint,"configuration fingerprint mismatch");
        let context=shake(&lp(&[b"CEQS12B/context",&fingerprint,&domain]),64);
        Ok(Self{fingerprint,domain,context,keys:ks})
    }

}
/// GF(2^512), modulus x^512+x^8+x^5+x^2+1, canonical big-endian field bytes.
fn scaled_challenge(c:&[u8],id:u64)->Vec<u8>{
    let mut v=[0u64;8];for(i,b)in c.chunks_exact(8).enumerate(){v[7-i]=u64::from_be_bytes(b.try_into().unwrap());}
    let mut out=[0u64;8];for j in 0..7{if id>>j&1==1{for i in 0..8{out[i]^=v[i];}}
        let carry=v[7]>>63;for i in(0..8).rev(){v[i]=(v[i]<<1)|if i>0{v[i-1]>>63}else{0};}if carry==1{v[0]^=0x125;}}
    out.iter().rev().flat_map(|x|x.to_be_bytes()).collect()
}
/// Concrete SHAKE circuit, not an ideal oracle inside the circuit.
/// Fixed-width SHAKE(label16 || seed48 || optional context64). Seed begins at word 2.
fn hash_seed<const OUT:usize>(b:&CircuitBuilder,label:&[u8],seed:&[Wire],suffix:&[&[u8]])->[Wire;OUT]{
    assert_eq!(label.len(),16);assert_eq!(seed.len(),6);assert!(OUT==8||OUT==16);
    let zero_seed=[0u8;48];let mut parts=vec![label,&zero_seed[..]];parts.extend_from_slice(suffix);
    let mut encoded:Vec<u8>=parts.concat();assert!(encoded.len()==64||encoded.len()==128);
    encoded.push(0x1f);while !encoded.len().is_multiple_of(136){encoded.push(0);}*encoded.last_mut().unwrap()^=0x80;
    let mut blocks:Vec<Wire>=words(&encoded).into_iter().map(|w|b.add_constant(w)).collect();
    for k in 0..6{blocks[2+k]=b.bxor(blocks[2+k],seed[k]);}
    let mut state:[Wire;25]=array::from_fn(|_|b.add_constant_64(0));
    for block in blocks.chunks_exact(17){for i in 0..17{state[i]=b.bxor(state[i],block[i]);}keccak_f1600(b,&mut state);}
    state[..OUT].try_into().unwrap()
}
pub fn validate_handles(bytes:&[u8],count:usize)->Result<()>{
    ensure!(bytes.len()==count*128,"wrong handle bytes");let hs:Vec<_>=bytes.chunks_exact(128).collect();
    ensure!(hs.windows(2).all(|p|p[0][..64]<p[1][..64]),"handles must have strictly increasing links");Ok(())
}
/// All lookups in a contribution consume the same six MSB selector wires.
fn lookup_word(b:&CircuitBuilder,table:&[Wire],selector:&[Wire;6])->Wire {
    assert_eq!(table.len(),64);let mut level=table.to_vec();
    for &bit in selector {level=level.chunks_exact(2).map(|pair|b.select(bit,pair[1],pair[0])).collect();}
    level[0]
}
fn lookup_words(b:&CircuitBuilder,table:&[Vec<Wire>],selector:&[Wire;6])->Vec<Wire>{
    (0..table[0].len()).map(|k|lookup_word(b,&table.iter().map(|row|row[k]).collect::<Vec<_>>(),selector)).collect()
}
pub fn circuit(cfg:&Config,message:&[u8],count:usize)->Result<(Circuit,Wires)>{
    ensure!(message.len()==64&&(1..=43).contains(&count),"message or diagnostic count");let b=CircuitBuilder::new();
    let registries:[Vec<Vec<Wire>>;2]=array::from_fn(|r|cfg.keys[r].iter().map(|key|words(key).into_iter().map(|x|b.add_constant(x)).collect()).collect());
    let challenge=message.to_vec();let scales:Vec<Vec<Wire>>=(1..=64).map(|i|words(&scaled_challenge(&challenge,i)).into_iter().map(|x|b.add_constant(x)).collect()).collect();
    let indicators:Vec<Wire>=(0..64).map(|i|b.add_constant_64(1u64<<i)).collect();
    let mut occupied=b.add_constant_64(0);
    let labels:[&[u8];2]=[b"CEQS12B/tracekey",b"CEQS12B/vote-key"];
    let mut wires=Wires{seats:vec![],seeds:vec![],public:vec![]};
    for j in 0..count{
        eprintln!("Constructing fusion contribution {}/{}",j+1,count);let sub=b.subcircuit(format!("fusion[{j}]"));
        let seat=b.add_witness();sub.assert_zero("seat_range",b.shr(seat,6));
        let selector:[Wire;6]=array::from_fn(|k|b.shl(seat,63-k as u32));
        let indicator=lookup_word(&b,&indicators,&selector);
        sub.assert_zero("seat_not_previously_occupied",b.band(occupied,indicator));
        occupied=b.bxor(occupied,indicator);
        let seeds:[Vec<Wire>;2]=array::from_fn(|_|(0..6).map(|_|b.add_witness()).collect());
        for role in 0..2{
            let expected=lookup_words(&b,&registries[role],&selector);let actual=hash_seed::<8>(&b,labels[role],&seeds[role],&[]);
            for k in 0..8{sub.assert_eq(format!("registered_role_{role}_{k}"),expected[k],actual[k]);}
        }
        let suffix=[cfg.context.as_slice()];
        let pair=hash_seed::<16>(&b,b"CEQS12B/pair-tag",&seeds[0],&suffix);
        let scaled=lookup_words(&b,&scales,&selector);
        for k in 0..16{let out=b.add_inout();let value=if k<8{pair[k]}else{b.bxor(pair[k],scaled[k-8])};sub.assert_eq(format!("public_handle_{k}"),out,value);wires.public.push(out);}
        wires.seats.push(seat);wires.seeds.push(seeds);
    }
    eprintln!("Lowering hash-fusion circuit");Ok((b.build(),wires))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn native_selector_and_occupancy_exhaustive_pairs() {
        let b=CircuitBuilder::new();
        let x=b.add_witness();let y=b.add_witness();
        b.assert_zero("x_range",b.shr(x,6));b.assert_zero("y_range",b.shr(y,6));
        let table:Vec<Wire>=(0..64).map(|i|b.add_constant_64(1u64<<i)).collect();
        let sx=array::from_fn(|k|b.shl(x,63-k as u32));
        let sy=array::from_fn(|k|b.shl(y,63-k as u32));
        let ex=lookup_word(&b,&table,&sx);let ey=lookup_word(&b,&table,&sy);
        let out=b.add_inout();b.assert_eq("one_hot_output",out,ex);
        b.assert_zero("disjoint",b.band(ex,ey));
        let c=b.build();
        for i in 0..64 {for j in 0..64 {
            let mut w=c.new_witness_filler();w[x]=Word(i);w[y]=Word(j);w[out]=Word(1u64<<i);
            let filled=c.populate_wire_witness(&mut w).is_ok();
            let valid=filled && c.constraint_system().verify(&w.into_value_vec()).is_ok();
            assert_eq!(valid,i!=j);
        }}
        for i in [64u64,65,127,1<<63,u64::MAX] {
            let mut w=c.new_witness_filler();w[x]=Word(i);w[y]=Word(i.wrapping_add(1)&63);w[out]=Word(1u64<<(i&63));
            let filled=c.populate_wire_witness(&mut w).is_ok();
            assert!(!filled || c.constraint_system().verify(&w.into_value_vec()).is_err());
        }
    }
    #[test]
    fn scale_matches_independent_python_vectors() {
        let cases:Value=serde_json::from_str(include_str!("../field_vectors.json")).unwrap();
        for case in cases.as_array().unwrap() {
            let c=unhex(case["message"].as_str().unwrap()).unwrap();
            let expected=unhex(case["product"].as_str().unwrap()).unwrap();
            assert_eq!(scaled_challenge(&c,case["identity"].as_u64().unwrap()),expected);
        }
    }
}
