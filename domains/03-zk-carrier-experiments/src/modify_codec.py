#!/usr/bin/env python3
"""The recorded mechanical edit that turns the QVT1 codec into the QVT2 codec.

The version 1.28 carrier was not written from scratch: its Rust codec was produced
from the version 1.27b codec by the string substitutions below. This script keeps
that edit executable, so the bytes at `history/v1.28/adapter/src/codec.rs` can be
re-derived from `src/adapter/src/codec_v1.rs` without a Rust toolchain.

It reads one Rust file and writes another; it never edits in place. `--output` is
required, because the QVT2 edit must not be applied over the current QVT3 codec at
`src/adapter/src/codec.rs`.
"""
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent


def transform(s):
    s = s.replace('//! QVT1: public transcript reconstruction for the pinned all-ZK trace component.', '//! QVT2: terminal-first affine reconstruction of public proof values.')
    s = s.replace('use binius_field::{Field,', 'use binius_field::{arithmetic_traits::InvertOrZero, Field,')
    s = s.replace('b"QVT1"', 'b"QVT2"')
    s = s.replace('original:Option<Vec<u8>>, prefix_len:usize,', 'original:Option<Vec<u8>>, prefix_len:usize, terminal_coeff:Vec<u8>, terminal_full:Vec<F>,')
    anchor = "struct Channel<'a> {"
    helper = '''fn expand_terminal(params:&FRIParams<F>,bytes:&[u8])->Result<Vec<F>> {
    let n=1usize<<params.n_final_challenges();let rate=params.rs_code().log_inv_rate();
    ensure!(bytes.len()==16*n,"terminal coefficient width");let coeff=read_scalars(bytes)?;
    let repeated:Vec<F>=coeff.iter().copied().cycle().take(n<<rate).collect();
    let dc=GaoMateerOnTheFly::<F>::generate(params.rs_code().log_len());
    let ntt=NeighborsLastReference{domain_context:dc};
    let mut b=FieldBuffer::<PackedGhash1x128b>::from_values(&repeated);
    ntt.forward_transform(b.as_mut_view(),rate,0);Ok(b.iter_scalars().collect())
}
'''
    s = s.replace(anchor, helper + anchor)
    s = s.replace('st.encoded.extend_from_slice(&pre);', 'st.encoded.extend_from_slice(&pre);\n                let coeff=st.terminal_coeff.clone();st.encoded.extend_from_slice(&coeff);')
    a = s.index('        for i in &unique {\n            let mut leaf=Vec::with_capacity(size);')
    b = s.index('        let boundary=frontier(depth,layer,&unique);', a)
    s = s[:a] + '''        let is_last=self.opening+1==self.params.input_oracles().len()+self.params.fold_arities().len();
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
''' + s[b:]
    s = s.replace('"transmitted_scalars":unique.len()*size-known.len(),"boundary_hashes":boundary.len()',
                  '"terminal_reconstructed_scalars":terminal_reconstructed,"transmitted_scalars":unique.len()*size-known.len()-terminal_reconstructed,"boundary_hashes":boundary.len()')
    s = s.replace('let coeff=inverse[..n].to_vec();st.encoded.extend_from_slice(&scalars(&coeff)?);coeff', 'let coeff=inverse[..n].to_vec();ensure!(scalars(&coeff)?==st.terminal_coeff,"preloaded terminal differs");coeff')
    s = s.replace('let pos=st.read_pos;let b=st.encoded.get(pos..pos+16*n).ok_or_else(||anyhow::anyhow!("truncated terminal"))?;\n            let coeff=read_scalars(b)?;st.read_pos+=16*n;coeff', 'read_scalars(&st.terminal_coeff)?')
    s = s.replace('ensure!(original.len()<=MAX_BYTES,"original limit");', '''ensure!(original.len()<=MAX_BYTES,"original limit");
    let (v1,_)=crate::codec_v1::encode(v,public,original)?;
    let terminal_bytes=16usize<<v.basefold_compiler().fri_params().n_final_challenges();
    ensure!(v1.len()>=terminal_bytes,"old terminal width");
    let terminal_coeff=v1[v1.len()-terminal_bytes..].to_vec();
    let terminal_full=expand_terminal(v.basefold_compiler().fri_params(),&terminal_coeff)?;''')
    s = s.replace('original:Some(original.to_vec()),prefix_len:0}', 'original:Some(original.to_vec()),prefix_len:0,terminal_coeff,terminal_full}')
    s = s.replace('"format":"QVT1"', '"format":"QVT2","terminal_preloaded":true,"previous_codec_bytes":v1.len(),"saved_from_previous_codec":v1.len()-st.encoded.len()')
    s = s.replace('    let st=Rc::new(RefCell::new(State{encoded:encoded.to_vec(),read_pos:HEADER+prefix,expanded:pre.clone(),report:vec![],original:None,prefix_len:prefix}));', '''    let terminal_bytes=16usize<<v.basefold_compiler().fri_params().n_final_challenges();
    let end=HEADER+prefix+terminal_bytes;ensure!(end<=encoded.len(),"missing preloaded terminal");
    let terminal_coeff=encoded[HEADER+prefix..end].to_vec();
    let terminal_full=expand_terminal(v.basefold_compiler().fri_params(),&terminal_coeff)?;
    let st=Rc::new(RefCell::new(State{encoded:encoded.to_vec(),read_pos:end,expanded:pre.clone(),report:vec![],original:None,prefix_len:prefix,terminal_coeff,terminal_full}));''')
    return s


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=HERE / 'adapter/src/codec_v1.rs',
                        help='the QVT1 codec (default: the retained version 1.27b codec)')
    parser.add_argument('--output', type=Path, required=True,
                        help='where to write the edited QVT2 codec')
    args = parser.parse_args()
    args.output.write_text(transform(args.input.read_text()))
    print(str(args.output))


if __name__ == '__main__':
    main()
