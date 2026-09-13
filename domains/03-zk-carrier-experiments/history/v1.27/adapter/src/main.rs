//! Experimental paired-trace, independent-authorization relation. No qualified signature or PQ theorem.
mod codec;
mod trace;
use std::{env,fs,path::Path,time::Instant};
use anyhow::{Result,ensure};
use binius_core::word::Word;
use binius_frontend::{Circuit,CircuitStat};
use binius_hash::StdHashSuite;
use binius_prover::{OptimalPackedB128,zk_config::ZKProver};
use binius_verifier::{config::StdChallenger,transcript::{ProverTranscript,VerifierTranscript},zk_config::ZKVerifier};
use serde_json::json;
use trace::{Config,Wires,words};
fn check(v:&ZKVerifier<StdHashSuite>,p:&[Word],proof:Vec<u8>)->Result<()>{let mut t=VerifierTranscript::new(StdChallenger::default(),proof);v.verify(p,&mut t)?;t.finalize()?;Ok(())}
fn fill(c:&Circuit,w:&Wires,private:&[Word],public:&[Word])->Result<binius_core::constraint_system::ValueVec>{
    ensure!(private.len()==w.seats.len()*13&&public.len()==w.public.len(),"witness dimensions");let mut f=c.new_witness_filler();
    for(j,part)in private.chunks_exact(13).enumerate(){f[w.seats[j]]=part[0];for role in 0..2{for k in 0..6{f[w.seeds[j][role][k]]=part[1+role*6+k];}}}
    for(w,value)in w.public.iter().zip(public){f[*w]=*value;}
    c.populate_wire_witness(&mut f)?;let value=f.into_value_vec();c.constraint_system().verify(&value)?;Ok(value)
}
fn frame(cfg:&Config,msg:&[u8],handles:&[u8],count:usize,rate:usize,encoded:&[u8])->Vec<u8>{
    let mut b=b"PT27".to_vec();b.extend_from_slice(&27u16.to_be_bytes());b.extend_from_slice(&(0x2700u16 | rate as u16).to_be_bytes());b.extend_from_slice(&cfg.fingerprint);b.extend_from_slice(&cfg.domain);b.extend_from_slice(msg);b.extend_from_slice(&(count as u16).to_be_bytes());b.extend_from_slice(&128u16.to_be_bytes());b.extend_from_slice(&(encoded.len()as u32).to_be_bytes());b.extend_from_slice(handles);b.extend_from_slice(encoded);b
}
fn main()->Result<()>{
    let args:Vec<String>=env::args().collect();ensure!(args.len()==7,"usage: adapter (stats|check|prove|prove_native|encode|verify) CONFIG_JSON PUBLIC_DIR PRIVATE_PATH COUNT RATE");
    let mode=&args[1];ensure!(["stats","check","prove","prove_native","encode","verify"].contains(&mode.as_str()),"mode");
    let cfg=Config::read(Path::new(&args[2]))?;let dir=Path::new(&args[3]);let count:usize=args[5].parse()?;let rate:usize=args[6].parse()?;
    ensure!((1..=43).contains(&count)&&(1..=4).contains(&rate),"diagnostic bounds");let start=Instant::now();
    let frame_path=dir.join(format!("trace{count}_rate{rate}.pt27"));let mut encoded=Vec::new();
    let (msg,handles)=if mode=="verify"{
        let b=fs::read(&frame_path)?;ensure!((208+128*count+16..=1048576+5712).contains(&b.len()),"frame size");
        ensure!(&b[..6]==b"PT27\x00\x1b"&&u16::from_be_bytes(b[6..8].try_into()?)==(0x2700u16 | rate as u16)&&b[8..72]==cfg.fingerprint&&b[72..136]==cfg.domain,"frame context or suite");
        ensure!(u16::from_be_bytes(b[200..202].try_into()?)as usize==count&&b[202..204]==[0,128],"frame threshold or handle width");
        let len=u32::from_be_bytes(b[204..208].try_into()?)as usize;ensure!(b.len()==208+128*count+len,"frame length");encoded=b[208+128*count..].to_vec();
        (b[136..200].to_vec(),b[208..208+128*count].to_vec())
    }else{let b=fs::read(dir.join("statement.bin"))?;ensure!(b.len()==64+128*count,"statement size");(b[..64].to_vec(),b[64..].to_vec())};
    trace::validate_handles(&handles,count)?;let public=words(&handles);
    let(c,w)=trace::circuit(&cfg,&msg,count)?;ensure!(c.inout()==w.public,"public wire order");let s=CircuitStat::collect(&c);
    let mut result=json!({"scope":"CEQS127_PAIRED_TRACE_RELATION_UNQUALIFIED","count":count,"seed_bytes_per_role":48,"hash_bytes":64,"field_bits":512,"setup_ceremony_qualified":false,
        "relation_version":"1.27","adapter_version":"1.27","injective_direct_message_challenge":true,"distinctness_method":"64_bit_occupancy_disjointness","same_hidden_seat_for_trace_and_authorization":true,"independent_authorization_seed":true,"paired_trace_output_bytes":128,"hidden_seat_range_and_distinctness":true,"complete_QC_verified":false,"ML_DSA_proved":false,"vote_key_preimage_constrained":true,"signature_of_knowledge_security_proved":false,"native_suite_security_label_bits":96,"qpt_128_qualified":false,"valid_QCs_generated":0,"LWR_matrix_constraints":0,"keccak_permutations_per_contribution":4,
        "stats":{"n_gates":s.n_gates,"n_and":s.n_and_constraints,"n_imul":s.n_imul_constraints,"n_zero":s.n_zero_constraints,"n_bmul":s.n_bmul_constraints,"n_witness":s.n_witness,"n_internal":s.n_internal,"n_inout":s.n_inout,"n_const":s.n_const,"committed_allocated":s.committed_allocated},"circuit_build_seconds":start.elapsed().as_secs_f64()});
    eprintln!("Unified circuit stats: {}",result["stats"]);
    if mode=="stats"{println!("{}",serde_json::to_string_pretty(&result)?);return Ok(());}
    let witness=if mode=="prove" || mode=="prove_native" || mode=="check"{
        let private=words(&fs::read(&args[4])?);let value=fill(&c,&w,&private,&public)?;result["constraints_verified"]=json!(true);
        if mode=="check"{
            let mut checks=vec!["honest_witness_matches_independent_fixture"];
            for case in 0..6{let mut p=private.clone();let mut out=public.clone();
                match case{0=>p[0]=Word(64),1=>p[1].0^=1,2=>p[7].0^=1,3=>p[0]=Word((p[0].0+1)%64),4=>out[8].0^=1,_=>out[0].0^=1};
                ensure!(fill(&c,&w,&p,&out).is_err(),"invalid paired witness accepted");checks.push(["seat_out_of_range","trace_seed_mutation","vote_seed_mutation","seat_reassignment","public_mask_mutation","public_link_mutation"][case]);}
            if count>1{
                for role in 0..2{let mut p=private.clone();let start=1+6*role;let other=private[13+start..13+start+6].to_vec();p[start..start+6].copy_from_slice(&other);ensure!(fill(&c,&w,&p,&public).is_err(),"cross-seat credential accepted");checks.push(["other_seat_trace_seed","other_seat_vote_seed"][role]);}
                let mut p=private.clone();let mut out=public.clone();let first=p[..13].to_vec();p[13..26].copy_from_slice(&first);let first_out=out[..16].to_vec();out[16..32].copy_from_slice(&first_out);ensure!(fill(&c,&w,&p,&out).is_err(),"duplicate complete contribution accepted");checks.push("duplicate_complete_contribution");
                let mut out=public.clone();let other_mask=out[24..32].to_vec();out[8..16].copy_from_slice(&other_mask);ensure!(fill(&c,&w,&private,&out).is_err(),"mixed link/mask accepted");checks.push("link_mask_from_different_seats");}
            result["constraint_checks"]=json!(checks);println!("{}",serde_json::to_string_pretty(&result)?);return Ok(());
        }Some(value)
    }else{None};
    eprintln!("Setting up ZK verifier");let t=Instant::now();let v=ZKVerifier::<StdHashSuite>::setup(c.constraint_system().clone(),rate)?;result["verifier_setup_seconds"]=json!(t.elapsed().as_secs_f64());drop(c);
    result["oracle_specs"]=json!(format!("{:?}",v.basefold_compiler().oracle_specs()));
    eprintln!("Oracle specs: {}", result["oracle_specs"]);
    if mode=="prove_native" {
        eprintln!("Setting up ZK prover for separate-process verification");
        let prover=ZKProver::<OptimalPackedB128,StdHashSuite>::setup(&v)?;
        drop(v);
        let mut t=ProverTranscript::new(StdChallenger::default());
        let clock=Instant::now();eprintln!("Producing native proof with verifier released");
        prover.prove(witness.as_ref().unwrap(),&mut rand::rng(),&mut t)?;
        let proof=t.finalize();
        fs::write(dir.join(format!("trace{count}_rate{rate}.proof")),&proof)?;
        result["proving_seconds"]=json!(clock.elapsed().as_secs_f64());
        result["native_proof_generated"]=json!(true);
        result["native_proof_verified"]=json!(false);
        result["requires_independent_verification"]=json!(true);
        result["native_proof_bytes"]=json!(proof.len());
        result["total_seconds"]=json!(start.elapsed().as_secs_f64());
        println!("{}",serde_json::to_string_pretty(&result)?);return Ok(());
    }
    if mode=="prove" || mode=="encode"{
        let proof=if mode=="prove" {
        eprintln!("Setting up ZK prover");let prover=ZKProver::<OptimalPackedB128,StdHashSuite>::setup(&v)?;
        let mut t=ProverTranscript::new(StdChallenger::default());let clock=Instant::now();eprintln!("Producing unified trace proof");prover.prove(witness.as_ref().unwrap(),&mut rand::rng(),&mut t)?;let proof=t.finalize();result["proving_seconds"]=json!(clock.elapsed().as_secs_f64());
        fs::write(dir.join(format!("trace{count}_rate{rate}.proof")),&proof)?;proof
        }else{fs::read(dir.join(format!("trace{count}_rate{rate}.proof")))?};
        check(&v,&public,proof.clone())?;result["native_proof_bytes"]=json!(proof.len());result["native_proof_verified"]=json!(true);
        eprintln!("Encoding unified trace proof");let(e,summary)=codec::encode(&v,&public,&proof)?;encoded=e;result["codec"]=summary;
        fs::write(&frame_path,frame(&cfg,&msg,&handles,count,rate,&encoded))?;
    }else{
        eprintln!("Decoding and verifying public-only trace frame");let proof=codec::decode(&v,&public,&encoded)?;result["native_proof_bytes"]=json!(proof.len());
        fs::write(dir.join(format!("trace{count}_rate{rate}.expanded")),&proof)?;
        result["public_only_verified"]=json!(true);result["private_input_opened"]=json!(false);
        let mut bad=public.clone();bad[8].0^=1;ensure!(codec::decode(&v,&bad,&encoded).is_err(),"altered mask accepted");result["changed_public_mask_rejected"]=json!(true);
    }
    result["full_quorum_relation_verified"]=json!(count==43);result["encoded_proof_bytes"]=json!(encoded.len());result["frame_bytes"]=json!(208+count*128+encoded.len());result["fits_32KiB"]=json!(208+count*128+encoded.len()<=32768);result["fits_512KiB"]=json!(208+count*128+encoded.len()<=524288);result["total_seconds"]=json!(start.elapsed().as_secs_f64());
    println!("{}",serde_json::to_string_pretty(&result)?);Ok(())
}
