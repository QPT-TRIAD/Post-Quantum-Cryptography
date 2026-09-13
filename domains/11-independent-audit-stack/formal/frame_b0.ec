(* frame_b0.ec — EasyCrypt game skeleton for FRAME on CE-QS profile B0.        *)
(* STATUS: UNEXECUTED. EasyCrypt is not installed on the authoring host; this   *)
(* file is the first game of the computational-formalisation stage and is       *)
(* checked only by careful reading. The proof is `admit`ted on purpose: it is a  *)
(* statement of the reduction to be machine-checked, not a claim that it was.   *)
(*                                                                              *)
(* Claim (v1.44 Theorem A, tight loss N = 64):                                  *)
(*   Pr[FRAME(A)] <= N * Pr[EUF-CMA(Sig, R(A))]                                 *)
(* where FRAME is won when extraction over two accepted B0 frames names a seat  *)
(* that signed at most one of the two conflicting vote messages.                *)

require import AllCore List FSet Distr DBool.

(* ---- abstract signature scheme ------------------------------------------ *)
type pkey, skey, sig, msg.
op N : int = 64.
op QUORUM : int = 43.

module type Scheme = {
  proc keygen() : pkey * skey
  proc sign(sk : skey, m : msg) : sig
  proc verify(pk : pkey, m : msg, s : sig) : bool
}.

(* EUF-CMA with a signing oracle; standard single-user game *)
module type EUF_Adv (O : Scheme) = {
  proc forge(pk : pkey) : msg * sig
}.

module EUF_CMA (S : Scheme) (A : EUF_Adv) = {
  var queried : msg fset
  module O = {
    proc sign(m : msg) : sig = {
      var s;
      queried <- queried `|` fset1 m;
      s <@ S.sign(EUF_CMA.sk, m);
      return s;
    }
  }
  var sk : skey
  proc main() : bool = {
    var pk, m, s, ok;
    queried <- fset0;
    (pk, sk) <@ S.keygen();
    (m, s) <@ A(O).forge(pk);
    ok <@ S.verify(pk, m, s);
    return ok /\ !(m \in queried);
  }
}.

(* ---- profile B0 ------------------------------------------------------------ *)
(* A frame is (domain, message, bitmap, signatures). vote i = prefix||cfg||domain||message||i.
   verify_b0 accepts iff popcount(bitmap) = QUORUM and every set seat's signature verifies
   over its vote under the registry key. extract_b0 = bitmap0 /\ bitmap1 when domains are
   equal and messages differ. A seat is FRAMED when it is in the intersection of two accepted
   frames but signed (through its honest signing oracle) at most one of the two vote messages. *)

type domain, message, bitmap.
op vote : domain -> message -> int -> msg.          (* domain-separated vote message of seat i *)
op popcount : bitmap -> int.
op bit : bitmap -> int -> bool.

module type Frame_Adv (O : Scheme) = {
  (* the adversary may corrupt seats (learn keys) and query honest seats' signing oracles;
     it outputs two frames. Corruption bookkeeping is in the game. *)
  proc corrupt(i : int) : skey
  proc frames() : (domain * message * bitmap * (int -> sig)) * (domain * message * bitmap * (int -> sig))
}.

module FRAME (S : Scheme) (A : Frame_Adv) = {
  var pks : int -> pkey
  var sks : int -> skey
  var corrupted : int fset
  var signed : (int * msg) fset            (* (seat, vote message) pairs signed by honest oracles *)
  module O = {
    proc sign(i : int, m : msg) : sig = {
      var s;
      signed <- signed `|` fset1 (i, m);
      s <@ S.sign(sks i, m);
      return s;
    }
  }
  proc accepts(f : domain * message * bitmap * (int -> sig)) : bool = {
    var d, m, b, sg, i, ok, all;
    (d, m, b, sg) <- f; all <- popcount b = QUORUM; i <- 0;
    while (i < N) {
      if (bit b i) { ok <@ S.verify(pks i, vote d m i, sg i); all <- all /\ ok; }
      i <- i + 1;
    }
    return all;
  }
  proc main() : bool = {
    var f0, f1, a0, a1, d0, m0, b0, s0, d1, m1, b1, s1, i, framed;
    corrupted <- fset0; signed <- fset0;
    i <- 0; while (i < N) { (pks i, sks i) <@ S.keygen(); i <- i + 1; }
    (f0, f1) <@ A(O).frames();
    a0 <@ accepts(f0); a1 <@ accepts(f1);
    (d0, m0, b0, s0) <- f0; (d1, m1, b1, s1) <- f1;
    framed <- false; i <- 0;
    while (i < N) {
      (* seat i is framed: in both bitmaps, honest, and did not sign both votes *)
      if (bit b0 i /\ bit b1 i /\ !(i \in corrupted) /\
          !((i, vote d0 m0 i) \in signed /\ (i, vote d1 m1 i) \in signed))
        framed <- true;
      i <- i + 1;
    }
    return a0 /\ a1 /\ d0 = d1 /\ m0 <> m1 /\ framed;
  }
}.

(* ---- reduction R: guess the framed seat j uniformly, embed the EUF-CMA key at j --------- *)
(* R answers A's signing queries for seat j through the EUF-CMA oracle and simulates all other
   seats with fresh keys. When A outputs frames that frame seat j, R outputs the vote message
   of the side j did not sign together with the signature in that frame: a fresh forgery.
   Guessing costs a factor N; nothing else is lost (tight, v1.44 Theorem A). *)

section.
declare module S <: Scheme.
declare module A <: Frame_Adv {-S}.

lemma frame_to_eufcma &m :
  Pr[FRAME(S, A).main() @ &m : res]
    <= N%r * Pr[EUF_CMA(S, R(A)).main() @ &m : res].
proof.
  (* Game hop 1: guess j <$ [0..N-1]; success preserved with probability 1/N when the guess
     equals a framed seat (there is at least one when FRAME wins).
     Game hop 2: replace seat j's key by the EUF-CMA challenge key; perfect simulation.
     Game hop 3: a framed seat j yields (m*, s*) with m* not queried at j; EUF-CMA wins. *)
  admit.
qed.
end section.

(* What this file does NOT say: it does not model SUPPRESS/EVADE/SAFETY (structural on B0, no
   reduction needed: bitmap public, intersection >= 2q - N by counting), and R is declared, not
   yet written as a concrete module. Next step: instantiate R, discharge the three hops. *)
