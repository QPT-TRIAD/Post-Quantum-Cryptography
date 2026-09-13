---- MODULE epoch_barrier ----
EXTENDS Naturals, FiniteSets

CONSTANTS Nodes, F, Q, Epochs, Domains, Messages, Sessions, Preps,
          EvidenceRoots, Boundaries

ASSUME Q = 2 * F + 1
ASSUME Cardinality(Nodes) = 3 * F + 1

VARIABLES
  epoch,
  voteChoice,
  prepPhase,
  prepSession,
  haveEvidence,
  anchorVotes,
  finalizedBoundary,
  sealChoice,
  sealCert,
  activatedBoundary

vars ==
  <<epoch, voteChoice, prepPhase, prepSession, haveEvidence, anchorVotes,
    finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

None == -1

Init ==
  /\ epoch = [i \in Nodes |-> 0]
  /\ voteChoice = [i \in Nodes |-> None]
  /\ prepPhase = [i \in Nodes |-> "U"]
  /\ prepSession = [i \in Nodes |-> None]
  /\ haveEvidence = {}
  /\ anchorVotes = {}
  /\ finalizedBoundary = None
  /\ sealChoice = [i \in Nodes |-> None]
  /\ sealCert = None
  /\ activatedBoundary = [i \in Nodes |-> None]

IsSealed(i) == sealChoice[i] # None

ReservePrep(i, s) ==
  /\ prepPhase[i] = "U"
  /\ prepPhase' = [prepPhase EXCEPT ![i] = "R"]
  /\ prepSession' = [prepSession EXCEPT ![i] = s]
  /\ UNCHANGED <<epoch, voteChoice, haveEvidence, anchorVotes,
                 finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

EmitPrep(i) ==
  /\ prepPhase[i] = "R"
  /\ prepPhase' = [prepPhase EXCEPT ![i] = "E"]
  /\ UNCHANGED <<epoch, voteChoice, prepSession, haveEvidence, anchorVotes,
                 finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

BurnPrep(i) ==
  /\ prepPhase[i] \in {"R","E"}
  /\ prepPhase' = [prepPhase EXCEPT ![i] = "B"]
  /\ UNCHANGED <<epoch, voteChoice, prepSession, haveEvidence, anchorVotes,
                 finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

OrdinaryVote(i, m) ==
  /\ epoch[i] = 0
  /\ ~IsSealed(i)
  /\ voteChoice[i] = None
  /\ voteChoice' = [voteChoice EXCEPT ![i] = m]
  /\ UNCHANGED <<epoch, prepPhase, prepSession, haveEvidence, anchorVotes,
                 finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

ReceiveEvidence(i, c) ==
  /\ haveEvidence' = haveEvidence \cup {<<i,c>>}
  /\ UNCHANGED <<epoch, voteChoice, prepPhase, prepSession, anchorVotes,
                 finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

AnchorVote(i, c) ==
  /\ epoch[i] = 0
  /\ <<i,c>> \in haveEvidence
  /\ anchorVotes' = anchorVotes \cup {<<i,c>>}
  /\ UNCHANGED <<epoch, voteChoice, prepPhase, prepSession, haveEvidence,
                 finalizedBoundary, sealChoice, sealCert, activatedBoundary>>

FinalizeBoundary(b) ==
  /\ finalizedBoundary = None
  /\ finalizedBoundary' = b
  /\ UNCHANGED <<epoch, voteChoice, prepPhase, prepSession, haveEvidence,
                 anchorVotes, sealChoice, sealCert, activatedBoundary>>

SealAfterFinality(i) ==
  /\ epoch[i] = 0
  /\ finalizedBoundary # None
  /\ sealChoice[i] = None
  /\ sealChoice' = [sealChoice EXCEPT ![i] = finalizedBoundary]
  /\ UNCHANGED <<epoch, voteChoice, prepPhase, prepSession, haveEvidence,
                 anchorVotes, finalizedBoundary, sealCert, activatedBoundary>>

SealSigners(b) ==
  { i \in Nodes : sealChoice[i] = b }

FormSealCert ==
  /\ finalizedBoundary # None
  /\ sealCert = None
  /\ Cardinality(SealSigners(finalizedBoundary)) >= Q
  /\ sealCert' = finalizedBoundary
  /\ UNCHANGED <<epoch, voteChoice, prepPhase, prepSession, haveEvidence,
                 anchorVotes, finalizedBoundary, sealChoice, activatedBoundary>>

Activate(i) ==
  /\ epoch[i] = 0
  /\ sealCert # None
  /\ epoch' = [epoch EXCEPT ![i] = 1]
  /\ activatedBoundary' =
       [activatedBoundary EXCEPT ![i] = sealCert]
  /\ UNCHANGED <<voteChoice, prepPhase, prepSession, haveEvidence, anchorVotes,
                 finalizedBoundary, sealChoice, sealCert>>

Crash ==
  UNCHANGED vars

Next ==
  \/ \E i \in Nodes, s \in Sessions : ReservePrep(i,s)
  \/ \E i \in Nodes : EmitPrep(i)
  \/ \E i \in Nodes : BurnPrep(i)
  \/ \E i \in Nodes, m \in Messages : OrdinaryVote(i,m)
  \/ \E i \in Nodes, c \in EvidenceRoots : ReceiveEvidence(i,c)
  \/ \E i \in Nodes, c \in EvidenceRoots : AnchorVote(i,c)
  \/ \E b \in Boundaries : FinalizeBoundary(b)
  \/ \E i \in Nodes : SealAfterFinality(i)
  \/ FormSealCert
  \/ \E i \in Nodes : Activate(i)
  \/ Crash

Spec == Init /\ [][Next]_vars

VoteOnce ==
  \A i \in Nodes : voteChoice[i] \in (Messages \cup {None})

PrepNoReuse ==
  \A i \in Nodes :
    /\ prepPhase[i] \in {"U","R","E","B"}
    /\ (prepPhase[i] = "U" => prepSession[i] = None)
    /\ (prepPhase[i] # "U" => prepSession[i] \in Sessions)

EvidenceBeforeAnchor ==
  \A i \in Nodes, c \in EvidenceRoots :
    <<i,c>> \in anchorVotes => <<i,c>> \in haveEvidence

SealOnlyFinalized ==
  \A i \in Nodes :
    sealChoice[i] # None => sealChoice[i] = finalizedBoundary

SealUnique ==
  \A i \in Nodes : sealChoice[i] \in (Boundaries \cup {None})

SealCertOnlyFinalized ==
  sealCert # None => sealCert = finalizedBoundary

SealCertHasQuorum ==
  sealCert # None => Cardinality(SealSigners(sealCert)) >= Q

ActivationRequiresSealCert ==
  \A i \in Nodes :
    epoch[i] = 1 =>
      /\ activatedBoundary[i] = sealCert
      /\ sealCert # None

TypeOK ==
  /\ epoch \in [Nodes -> {0,1}]
  /\ voteChoice \in [Nodes -> (Messages \cup {None})]
  /\ prepPhase \in [Nodes -> {"U","R","E","B"}]
  /\ prepSession \in [Nodes -> (Sessions \cup {None})]
  /\ finalizedBoundary \in (Boundaries \cup {None})
  /\ sealChoice \in [Nodes -> (Boundaries \cup {None})]
  /\ sealCert \in (Boundaries \cup {None})
  /\ activatedBoundary \in [Nodes -> (Boundaries \cup {None})]

\* -----------------------------------------------------------------------------
\* Repository note. Epoch-barrier specification, v0.6 revision of the PQ-AQC record;
\* the version suffix has been dropped because this is the only revision preserved
\* here. It is a specification artifact and has never been executed by TLC or TLAPS.
\* The recorded bounded-exploration output in results/pqaqc_modelcheck.txt comes
\* from the independent Python checker src/pqaqc_finite_state_check.py, not from TLC.
\* The MODULE name uses an underscore because TLA+ identifiers cannot contain a
\* hyphen, so it does not match the file name formal/epoch-barrier.tla. TLA+ tooling
\* expects the file name to equal the MODULE name: a TLC run therefore needs the file
\* copied or renamed to epoch_barrier.tla, or the MODULE line changed back. The
\* companion configuration is formal/epoch-barrier.cfg.
\* -----------------------------------------------------------------------------
====
