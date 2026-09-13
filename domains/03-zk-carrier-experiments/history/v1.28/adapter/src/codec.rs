//! QVT2: terminal-first affine reconstruction of public proof values.
//! Experimental codec, not a new proof of knowledge or a qualified quorum verifier.
//! Folding and verification operations use pinned Binius public APIs.
use std::{cell::RefCell, collections::{BTreeMap, BTreeSet}, rc::Rc};
use anyhow::{Result, ensure};
use binius_core::word::Word;
use binius_field::{arithmetic_traits::InvertOrZero, Field, Ghash128b as F, PackedGhash1x128b};
use binius_hash::{StdHashSuite, StdDigest, StdCompression, CompressionFunction, hash_serialize};
use binius_iop::{fri::{FRIParams, fold::fold_chunk}, merkle_channel::{MerkleIPVerifierChannel, VerifierMerkleTranscriptChannel, Error as MerkleError}};
use binius_ip::channel::{IPVerifierChannel, WordIPVerifierChannel, Error as IpError};
use binius_math::{FieldBuffer, multilinear::{eq::eq_ind_partial_eval_scalars, evaluate::evaluate_inplace_scalars}, ntt::{AdditiveNTT, NeighborsLastReference, domain_context::GaoMateerOnTheFly}};
use binius_spartan_verifier::wrapper::ZKWrappedVerifierChannel;
use binius_transcript::VerifierTranscript;
use binius_utils::{SerializeBytes, DeserializeBytes};
use binius_verifier::{config::StdChallenger, protocols::shift::WiringEvalClaim, zk_config::ZKVerifier};
use bytes::Buf;
use digest::Output;
use serde_json::{Value, json};

type Tape = VerifierTranscript<StdChallenger>;
type Native<'a> = VerifierMerkleTranscriptChannel<&'a mut Tape, StdChallenger, F, StdHashSuite>;
type Commitment = <Native<'static> as MerkleIPVerifierChannel<F>>::Commitment;
type Hash = Output<StdDigest>;
type Nodes = BTreeMap<(usize,usize),Hash>;
const MAGIC: &[u8;4] = b"QVT2";
const MAX_BYTES: usize = 1 << 20; // fixed diagnostic bound, not the QC admission limit
const HEADER: usize = 16;

fn scalars(values: &[F]) -> Result<Vec<u8>> {
    let mut b=Vec::with_capacity(values.len()*16);
    for v in values { v.serialize(&mut b)?; }
    Ok(b)
}
fn read_scalars(bytes:&[u8])->Result<Vec<F>> {
    ensure!(bytes.len().is_multiple_of(16), "bad field byte count");
    let mut s=bytes; let mut out=Vec::new();
    while !s.is_empty() {out.push(F::deserialize(&mut s)?);}
    Ok(out)
}
fn take<'a>(data:&'a [u8],pos:&mut usize,n:usize)->Result<&'a [u8]>{
    let end=pos.checked_add(n).ok_or_else(||anyhow::anyhow!("length overflow"))?;
    ensure!(end<=data.len(),"truncated codec");let b=&data[*pos..end];*pos=end;Ok(b)
}
fn frontier(depth:usize,layer:usize,unique:&BTreeSet<usize>)->Vec<(usize,usize)>{
    fn visit(d:usize,i:usize,depth:usize,u:&BTreeSet<usize>,out:&mut Vec<(usize,usize)>){
        let lo=i<<(depth-d);let hi=(i+1)<<(depth-d);
        if u.range(lo..hi).next().is_none(){out.push((d,i));}
        else if d<depth {visit(d+1,2*i,depth,u,out);visit(d+1,2*i+1,depth,u,out);}
    }
    let mut out=Vec::new();for i in 0..1<<layer {visit(layer,i,depth,unique,&mut out);}out
}
fn node(nodes:&mut Nodes,d:usize,i:usize,depth:usize)->Result<Hash>{
    if let Some(h)=nodes.get(&(d,i)){return Ok(h.clone());}
    ensure!(d<depth,"missing leaf node");
    let left=node(nodes,d+1,2*i,depth)?;let right=node(nodes,d+1,2*i+1,depth)?;
    let h=StdCompression::default().compress([left,right]);nodes.insert((d,i),h.clone());Ok(h)
}
struct State {
    encoded: Vec<u8>, read_pos: usize, expanded: Vec<u8>, report:Vec<Value>,
    original:Option<Vec<u8>>, prefix_len:usize, terminal_coeff:Vec<u8>, terminal_full:Vec<F>,
}
fn expand_terminal(params:&FRIParams<F>,bytes:&[u8])->Result<Vec<F>> {
    let n=1usize<<params.n_final_challenges();let rate=params.rs_code().log_inv_rate();
    ensure!(bytes.len()==16*n,"terminal coefficient width");let coeff=read_scalars(bytes)?;
    let repeated:Vec<F>=coeff.iter().copied().cycle().take(n<<rate).collect();
    let dc=GaoMateerOnTheFly::<F>::generate(params.rs_code().log_len());
    let ntt=NeighborsLastReference{domain_context:dc};
    let mut b=FieldBuffer::<PackedGhash1x128b>::from_values(&repeated);
    ntt.forward_transform(b.as_mut_view(),rate,0);Ok(b.iter_scalars().collect())
}
struct Channel<'a> {
    tape:&'a mut Tape, total:usize, state:Rc<RefCell<State>>, params:&'a FRIParams<F>,
    samples:Vec<F>, query_indices:Vec<Word>, opening:usize, claims:Vec<F>, prev:Vec<usize>,
    gamma:F, weights:Vec<F>, fold_challenges:Vec<F>, fold_offset:usize,
}
impl Channel<'_> {
    fn native(&mut self)->Native<'_>{Native::new(&mut *self.tape)}
    fn position(&mut self)->usize{self.total-self.tape.decommitment().buffer().remaining()}
    fn init_queries(&mut self)->Result<()> {
        let n=self.params.rs_code().log_dim();
        let count=self.params.input_oracles().len();
        let outer=count.next_power_of_two().trailing_zeros() as usize;
        ensure!(count>0 && self.params.log_batch_size()==1+outer,"unsupported oracle shape");
        ensure!(self.params.input_oracles().iter().all(|s|s.log_early_batch_size==1 && s.log_later_batch_size==0),"only all-ZK shape supported");
        let needed=2*n+outer+2;
        ensure!(self.samples.len()>=needed,"missing public challenge history");
        let k=self.samples.len();
        // Pinned basefold/channel.rs: gamma, phase-A batch coefficient, n challenges,
        // ceil(log2(oracle_count)) outer challenges, then n phase-B folding challenges.
        self.gamma=self.samples[k-needed];
        self.weights=eq_ind_partial_eval_scalars(&self.samples[k-n-outer..k-n]);
        self.fold_challenges=self.samples[k-n..].to_vec();
        ensure!(self.query_indices.len()==self.params.n_test_queries(),"unexpected query sampling schedule");
        self.prev=self.query_indices.iter().map(|i|i.0 as usize).collect();
        self.claims=vec![F::ZERO;self.prev.len()];
        Ok(())
    }
    fn openings(&mut self,c:&Commitment,indices:&[Word])->Result<Vec<F>> {
        if self.opening==0 {self.init_queries()?;}
        let depth=c.commitment.depth;let size=c.leaf_size;
        let layer=(indices.len().next_power_of_two().trailing_zeros() as usize).min(depth);
        let ix:Vec<usize>=indices.iter().map(|i|i.0 as usize).collect();
        ensure!(ix.len()==self.prev.len() && ix.iter().all(|i|*i<1<<depth),"query shape");
        let unique:BTreeSet<_>=ix.iter().copied().collect();
        let mut known:BTreeMap<(usize,usize),F>=BTreeMap::new();
        if self.opening>=self.params.input_oracles().len() {
            let a=self.params.fold_arities()[self.opening-self.params.input_oracles().len()];ensure!(size==1<<a,"fold leaf size");
            for q in 0..ix.len(){
                ensure!(ix[q]==self.prev[q]>>a,"fold index mismatch");
                let key=(ix[q],self.prev[q]&(size-1));
                if let Some(old)=known.insert(key,self.claims[q]){ensure!(old==self.claims[q],"inconsistent repeated claim");}
            }
        } else {
            let s=&self.params.input_oracles()[self.opening];
            ensure!(size==2 && ix.iter().zip(&self.prev).all(|(i,j)|*i==*j>>s.log_lift),"input index mismatch");
        }
        let encoding=self.state.borrow().original.is_some();
        let mut leaves:BTreeMap<usize,Vec<F>>=BTreeMap::new();let mut nodes=Nodes::new();
        let native_start=self.position();
        let original_values=if encoding {
            let v=self.native().recv_openings(c,indices)?;
            let end=self.position();let mut st=self.state.borrow_mut();
            if self.opening==0 {
                st.prefix_len=native_start;st.expanded=st.original.as_ref().unwrap()[..native_start].to_vec();
                st.encoded.resize(HEADER,0);let pre=st.expanded.clone();st.encoded.extend_from_slice(&pre);
                let coeff=st.terminal_coeff.clone();st.encoded.extend_from_slice(&coeff);
            }
            let raw=&st.original.as_ref().unwrap()[native_start..end];let mut off=0;
            for i in 0..1<<layer {nodes.insert((layer,i),Hash::try_from(take(raw,&mut off,32)?).unwrap());}
            for (q,i) in ix.iter().copied().enumerate(){
                take(raw,&mut off,16*size)?;
                let leaf=v[q*size..(q+1)*size].to_vec();
                if let Some(old)=leaves.insert(i,leaf.clone()){ensure!(old==leaf,"duplicate leaf conflict");}
                nodes.insert((depth,i),hash_serialize::<F,StdDigest>(&leaf)?);
                for d in (layer+1..=depth).rev(){
                    let sibling=(i>>(depth-d))^1;
                    let h=Hash::try_from(take(raw,&mut off,32)?).unwrap();
                    if let Some(old)=nodes.insert((d,sibling),h.clone()){ensure!(old==h,"duplicate path conflict");}
                }
            }
            ensure!(off==raw.len(),"native advice accounting");Some(v)
        } else {None};
        let mut st=self.state.borrow_mut();let before=if encoding{st.encoded.len()}else{st.read_pos};
        if !encoding && self.opening==0 {ensure!(native_start==st.prefix_len,"prefix boundary mismatch");}
        let is_last=self.opening+1==self.params.input_oracles().len()+self.params.fold_arities().len();
        let mut terminal_reconstructed=0usize;
        let dc=GaoMateerOnTheFly::<F>::generate(self.params.rs_code().log_len());
        for i in &unique {
            // The outgoing fold is linear. The fully disclosed terminal determines its value.
            let weights:Vec<F>=if is_last {
                let a=self.params.fold_arities()[self.opening-self.params.input_oracles().len()];
                let challenges=&self.fold_challenges[self.fold_offset..self.fold_offset+a];
                (0..size).map(|j|{let mut unit=vec![F::ZERO;size];unit[j]=F::ONE;
                    fold_chunk(&NeighborsLastReference{domain_context:&dc},depth+a,*i,&mut unit,challenges)}).collect()
            }else{vec![]};
            let pivot=if is_last {(0..size).find(|j|!known.contains_key(&(*i,*j)) && weights[*j]!=F::ZERO)}else{None};
            let mut leaf=Vec::with_capacity(size);
            for j in 0..size {
                let value=if Some(j)==pivot {F::ZERO} else if let Some(value)=known.get(&(*i,j)) {
                    if encoding {ensure!(leaves[i][j]==*value,"reconstructed scalar differs");}
                    *value
                } else if encoding {
                    let value=leaves[i][j];value.serialize(&mut st.encoded)?;value
                } else {
                    let pos=st.read_pos;let b=st.encoded.get(pos..pos+16).ok_or_else(||anyhow::anyhow!("truncated field"))?;
                    let value=F::deserialize(b)?;st.read_pos+=16;value
                };leaf.push(value);
            }
            if is_last {
                let target=*st.terminal_full.get(*i).ok_or_else(||anyhow::anyhow!("terminal index"))?;
                let sum: F=weights.iter().zip(&leaf).map(|(w,x)|*w * *x).sum();
                if let Some(j)=pivot {
                    leaf[j]=(target-sum)*weights[j].invert_or_zero();
                    if encoding {ensure!(leaf[j]==leaves[i][j],"terminal-derived scalar differs");}
                    terminal_reconstructed+=1;
                }else{ensure!(sum==target,"fully known outgoing fold differs");}
            }
            if !encoding {nodes.insert((depth,*i),hash_serialize::<F,StdDigest>(&leaf)?);leaves.insert(*i,leaf);}
        }
        let boundary=frontier(depth,layer,&unique);
        for &(d,i) in &boundary {
            if encoding {let h=node(&mut nodes,d,i,depth)?;st.encoded.extend_from_slice(&h);}
            else {let pos=st.read_pos;let b=st.encoded.get(pos..pos+32).ok_or_else(||anyhow::anyhow!("truncated hash"))?;
                nodes.insert((d,i),Hash::try_from(b).unwrap());st.read_pos+=32;}
        }
        let mut advice=Vec::new();
        for i in 0..1<<layer {advice.extend_from_slice(&node(&mut nodes,layer,i,depth)?);}
        let mut values=Vec::new();
        for i in &ix {
            advice.extend_from_slice(&scalars(&leaves[i])?);values.extend_from_slice(&leaves[i]);
            for d in (layer+1..=depth).rev(){advice.extend_from_slice(&node(&mut nodes,d,(i>>(depth-d))^1,depth)?);}
        }
        if let Some(v)=original_values {ensure!(values==v,"query values changed");
            let raw=&st.original.as_ref().unwrap()[native_start..self.total-self.tape.decommitment().buffer().remaining()];
            ensure!(advice==raw,"advice expansion differs");
        } else {
            let mut t=Tape::new(StdChallenger::default(),advice.clone());
            let verified=Native::new(&mut t).recv_openings(c,indices)?;t.finalize()?;
            ensure!(verified==values,"native values differ");
        }
        st.expanded.extend_from_slice(&advice);
        let after=if encoding{st.encoded.len()}else{st.read_pos};
        st.report.push(json!({"opening":self.opening,"native_advice_bytes":advice.len(),
            "encoded_bytes":after-before,"unique_leaves":unique.len(),"query_count":ix.len(),
            "leaf_scalars":size,"reconstructed_scalars":known.len(),
            "terminal_reconstructed_scalars":terminal_reconstructed,"transmitted_scalars":unique.len()*size-known.len()-terminal_reconstructed,"boundary_hashes":boundary.len()}));
        drop(st);
        if self.opening<self.params.input_oracles().len() {
            for q in 0..ix.len(){self.claims[q]+=evaluate_inplace_scalars(values[q*size..(q+1)*size].to_vec(),&[self.gamma])*self.weights[self.opening];}
        } else {
            let a=self.params.fold_arities()[self.opening-self.params.input_oracles().len()];
            let challenges=self.fold_challenges[self.fold_offset..self.fold_offset+a].to_vec();
            let dc=GaoMateerOnTheFly::<F>::generate(self.params.rs_code().log_len());
            for q in 0..ix.len(){
                self.claims[q]=fold_chunk(&NeighborsLastReference{domain_context:&dc},depth+a,ix[q],&mut values[q*size..(q+1)*size].to_vec(),&challenges);
            }
            self.fold_offset+=a;self.prev=ix;
        }
        self.opening+=1;Ok(values)
    }
    fn terminal(&mut self,c:&Commitment)->Result<Vec<F>> {
        ensure!(self.opening==self.params.input_oracles().len()+self.params.fold_arities().len(),"terminal schedule");
        let n=c.leaf_size;let rate=c.commitment.depth;
        ensure!(n==1<<self.params.n_final_challenges() && rate==self.params.rs_code().log_inv_rate(),"terminal shape");
        let dc=GaoMateerOnTheFly::<F>::generate(self.params.rs_code().log_len());
        let ntt=NeighborsLastReference{domain_context:dc};
        let encoding=self.state.borrow().original.is_some();
        let full=if encoding{Some(self.native().recv_committed_vector(c)?)}else{None};
        let mut st=self.state.borrow_mut();
        let coeff=if let Some(ref full)=full{
            let mut b=FieldBuffer::<PackedGhash1x128b>::from_values(full);
            ntt.inverse_transform(b.as_mut_view(),rate,0);
            let inverse:Vec<F>=b.iter_scalars().collect();
            ensure!(inverse.chunks(n).all(|v|v==&inverse[..n]),"terminal is outside compact codeword subspace");
            let coeff=inverse[..n].to_vec();ensure!(scalars(&coeff)?==st.terminal_coeff,"preloaded terminal differs");coeff
        } else {
            read_scalars(&st.terminal_coeff)?
        };
        let repeated:Vec<F>=coeff.iter().copied().cycle().take(n<<rate).collect();
        let mut b=FieldBuffer::<PackedGhash1x128b>::from_values(&repeated);
        ntt.forward_transform(b.as_mut_view(),rate,0);
        let expanded:Vec<F>=b.iter_scalars().collect();let advice=scalars(&expanded)?;
        if let Some(full)=full{ensure!(full==expanded,"terminal expansion differs");}
        else {let mut t=Tape::new(StdChallenger::default(),advice.clone());
            ensure!(Native::new(&mut t).recv_committed_vector(c)?==expanded,"terminal native mismatch");t.finalize()?;}
        st.expanded.extend_from_slice(&advice);
        st.report.push(json!({"terminal_native_bytes":advice.len(),"terminal_encoded_bytes":16*n}));
        Ok(expanded)
    }
}
impl IPVerifierChannel<F> for Channel<'_> {
    type Elem=F;
    fn recv_one(&mut self)->Result<F,IpError>{self.native().recv_one()}
    fn recv_many(&mut self,n:usize)->Result<Vec<F>,IpError>{self.native().recv_many(n)}
    fn recv_array<const N:usize>(&mut self)->Result<[F;N],IpError>{self.native().recv_array()}
    fn sample(&mut self)->F{let x=self.native().sample();self.samples.push(x);x}
    fn observe_one(&mut self,x:F)->F{self.native().observe_one(x)}
    fn observe_many(&mut self,x:&[F])->Vec<F>{self.native().observe_many(x)}
    fn assert_zero(&mut self,x:F)->Result<(),IpError>{self.native().assert_zero(x)}
}
impl WordIPVerifierChannel<F> for Channel<'_> {
    type Word=Word;
    fn observe_words(&mut self,x:&[Word])->Vec<Word>{self.native().observe_words(x)}
    fn subset_sum(&mut self,x:&[F],w:&Word)->F{self.native().subset_sum(x,w)}
    fn select(&mut self,x:&[F],w:&Word)->F{self.native().select(x,w)}
    fn sample_bits(&mut self,b:usize)->Word{let w=self.native().sample_bits(b);self.query_indices.push(w);w}
    fn pack_words(&mut self,w:&[Word])->Vec<F>{self.native().pack_words(w)}
}
fn merr(e:anyhow::Error)->MerkleError{eprintln!("codec rejection: {e:#}");MerkleError::IPChannel(IpError::InvalidAssert)}
impl MerkleIPVerifierChannel<F> for Channel<'_> {
    type Commitment=Commitment;
    fn recv_merkle_commitment(&mut self,s:usize,d:usize)->Result<Commitment,MerkleError>{self.native().recv_merkle_commitment(s,d)}
    fn recv_openings(&mut self,c:&Commitment,i:&[Word])->Result<Vec<F>,MerkleError>{self.openings(c,i).map_err(merr)}
    fn recv_committed_vector(&mut self,c:&Commitment)->Result<Vec<F>,MerkleError>{self.terminal(c).map_err(merr)}
}
fn run(v:&ZKVerifier<StdHashSuite>,public:&[Word],tape_bytes:Vec<u8>,st:Rc<RefCell<State>>)->Result<()> {
    let total=tape_bytes.len();let mut tape=Tape::new(StdChallenger::default(),tape_bytes);
    let channel=Channel{tape:&mut tape,total,state:st,params:v.basefold_compiler().fri_params(),samples:vec![],query_indices:vec![],opening:0,claims:vec![],prev:vec![],gamma:F::ZERO,weights:vec![],fold_challenges:vec![],fold_offset:0};
    let channel=v.basefold_compiler().create_channel(channel);
    let mut wrapped=ZKWrappedVerifierChannel::new(channel,v.outer_iop_verifier(),v.outer_layout_arc())?;
    let inout=wrapped.observe_words(public);
    let claim=v.inner_iop_verifier().verify(&inout,&mut wrapped)?;
    let public_value=|elem|wrapped.public_value(elem).expect("public wiring claim");
    WiringEvalClaim{inputs:claim.inputs.iter().map(public_value).collect(),claimed:public_value(&claim.claimed),eval_fn:claim.eval_fn}.check_native()?;
    wrapped.finish()?;tape.finalize()?;Ok(())
}
pub fn encode(v:&ZKVerifier<StdHashSuite>,public:&[Word],original:&[u8])->Result<(Vec<u8>,Value)> {
    ensure!(original.len()<=MAX_BYTES,"original limit");
    let (v1,_)=crate::codec_v1::encode(v,public,original)?;
    let terminal_bytes=16usize<<v.basefold_compiler().fri_params().n_final_challenges();
    ensure!(v1.len()>=terminal_bytes,"old terminal width");
    let terminal_coeff=v1[v1.len()-terminal_bytes..].to_vec();
    let terminal_full=expand_terminal(v.basefold_compiler().fri_params(),&terminal_coeff)?;
    let st=Rc::new(RefCell::new(State{encoded:vec![],read_pos:0,expanded:vec![],report:vec![],original:Some(original.to_vec()),prefix_len:0,terminal_coeff,terminal_full}));
    run(v,public,original.to_vec(),st.clone())?;
    let mut st=st.borrow_mut();ensure!(st.expanded==original,"complete byte-exact expansion failed");
    let prefix=st.prefix_len as u32;let expanded=original.len() as u32;
    st.encoded[..4].copy_from_slice(MAGIC);st.encoded[4]=v.log_inv_rate() as u8;
    st.encoded[8..12].copy_from_slice(&prefix.to_le_bytes());st.encoded[12..16].copy_from_slice(&expanded.to_le_bytes());
    let report=json!({"scope":"EXACT_NATIVE_TRANSCRIPT_CODEC_UNQUALIFIED","format":"QVT2","terminal_preloaded":true,"previous_codec_bytes":v1.len(),"saved_from_previous_codec":v1.len()-st.encoded.len(),"input_oracle_count":v.basefold_compiler().fri_params().input_oracles().len(),"original_bytes":original.len(),
        "encoded_bytes":st.encoded.len(),"header_bytes":HEADER,"native_prefix_bytes":prefix,
        "saved_bytes":original.len()-st.encoded.len(),"encoded_plus_43_handle_envelope_bytes":st.encoded.len()+5712,
        "proof_payload_budget":27056,"fits_budget":st.encoded.len()<=27056,"roundtrip_byte_exact":true,
        "public_statement_only":true,"all_native_checks_retained":true,"qpt_128_qualified":false,
        "valid_quorum_certificates":0,"sections":st.report});
    Ok((st.encoded.clone(),report))
}
pub fn decode(v:&ZKVerifier<StdHashSuite>,public:&[Word],encoded:&[u8])->Result<Vec<u8>> {
    ensure!((HEADER..=MAX_BYTES).contains(&encoded.len()),"encoded length");
    ensure!(&encoded[..4]==MAGIC && encoded[4] as usize==v.log_inv_rate() && encoded[5..8]==[0,0,0],"codec header");
    let prefix=u32::from_le_bytes(encoded[8..12].try_into()?) as usize;
    let total=u32::from_le_bytes(encoded[12..16].try_into()?) as usize;
    ensure!(prefix<=MAX_BYTES && total<=MAX_BYTES && prefix<=total && HEADER+prefix<=encoded.len(),"bounded sizes");
    let pre=encoded[HEADER..HEADER+prefix].to_vec();
    let terminal_bytes=16usize<<v.basefold_compiler().fri_params().n_final_challenges();
    let end=HEADER+prefix+terminal_bytes;ensure!(end<=encoded.len(),"missing preloaded terminal");
    let terminal_coeff=encoded[HEADER+prefix..end].to_vec();
    let terminal_full=expand_terminal(v.basefold_compiler().fri_params(),&terminal_coeff)?;
    let st=Rc::new(RefCell::new(State{encoded:encoded.to_vec(),read_pos:end,expanded:pre.clone(),report:vec![],original:None,prefix_len:prefix,terminal_coeff,terminal_full}));
    run(v,public,pre,st.clone())?;
    let st=st.borrow();ensure!(st.read_pos==encoded.len(),"trailing codec data");ensure!(st.expanded.len()==total,"expanded length mismatch");
    // A separate, ordinary upstream verification is mandatory at the public entry point.
    let mut t=Tape::new(StdChallenger::default(),st.expanded.clone());v.verify(public,&mut t)?;t.finalize()?;
    Ok(st.expanded.clone())
}
