-- ============================================================
-- Seed: Ari's first 10 B2B calls — 2026-09-14, ~3pm Sydney
-- All to direct mobiles. Source: Ari's verbal feedback.
-- append-only: these are attempt_no=1 for each account.
-- ============================================================

INSERT INTO painting_call_log
(call_id, account_id, called_at, call_window, caller, channel, number_called, person_called,
 outcome_code, outcome_note, loss_reason, next_action, next_action_at, recall_after, attempt_no, created_at)
VALUES

-- #1 Dynamic Property — no answer
('lead:call:dynamic-20260914-1','lead:acct:dynamic-property-services-pica-group','2026-09-14T15:00:00','afternoon','ari','mobile','0436 404 601','Marlena Basa (BDM)',
 'N','','','retry in a different time window','','',1,'2026-09-14T15:00:00'),

-- #2 Jamesons — no answer
('lead:call:jamesons-20260914-1','lead:acct:jamesons-strata-management','2026-09-14T15:00:00','afternoon','ari','mobile','0485 870 404','Lilla Kelemen (CEO)',
 'N','','','retry in a different time window','','',1,'2026-09-14T15:00:00'),

-- #3 IB Property — no answer
('lead:call:ibproperty-20260914-1','lead:acct:ib-property','2026-09-14T15:00:00','afternoon','ari','mobile','0438 451 846','Nick Warren (Head of FM)',
 'N','','','retry in a different time window','','',1,'2026-09-14T15:00:00'),

-- #4 BCS Strata — no answer
('lead:call:bcs-20260914-1','lead:acct:bcs-strata-sydney-pica-group','2026-09-14T15:00:00','afternoon','ari','mobile','0427 160 092','Ryan Hewit (BDM)',
 'N','','','retry in a different time window','','',1,'2026-09-14T15:00:00'),

-- #5 Alldis and Cox — no answer
('lead:call:alldis-20260914-1','lead:acct:alldis-and-cox','2026-09-14T15:00:00','afternoon','ari','mobile','0499 038 901','Murray Cox',
 'N','','','retry in a different time window','','',1,'2026-09-14T15:00:00'),

-- #6 ESR Group — no answer
('lead:call:esr-20260914-1','lead:acct:esr-group','2026-09-14T15:00:00','afternoon','ari','mobile','0415 784 898','Fergus Adamson (GM Property NSW)',
 'N','','','retry in a different time window','','',1,'2026-09-14T15:00:00'),

-- #7 Sara Strata — POSITIVE, asked for email
('lead:call:sarastrata-20260914-1','lead:acct:sara-strata','2026-09-14T15:00:00','afternoon','ari','mobile','0485 007 960','Tim Sara (Principal)',
 'E','Answered, receptive. Asked us to send details to his email, said it is useful and he will stay in touch.','','SEND EMAIL — fact-only intro + capability. Confirm his email address.','2026-09-15','',1,'2026-09-14T15:00:00'),

-- #8 One Strata Managers — OPS_FAIL, interested lead lost
('lead:call:onestrata-20260914-1','lead:acct:one-strata-managers','2026-09-14T15:00:00','afternoon','ari','mobile','0421 309 740','Christian Olivos (Principal Licensee)',
 'OPS_FAIL','Was dictating his email address (i.e. INTERESTED). Ari had no pen ready, said so, contact got annoyed and hung up. Lead was qualified — lost to lack of preparation, not to the market.','not prepared to capture email','RE-CALL with pen/screen ready. Apologise briefly, ask to resend email.','2026-09-21','',1,'2026-09-14T15:00:00'),

-- #9 TalentWeb (Donny) — WRONG_SEGMENT
('lead:call:talentweb-20260914-1','lead:acct:talentweb-property-donny-mudiasa','2026-09-14T15:00:00','afternoon','ari','mobile','0430 010 756','Donny Mudiasa (FM Recruiter)',
 'WRONG_SEGMENT','Ari asked if they are strata; they said no, we are recruiters. Our classification error — Donny is an FM recruiter, not a strata client.','not a strata/painting client — recruiter','Fix segment in DB. Possible referral channel later, not a direct client.','','',1,'2026-09-14T15:00:00'),

-- #10 Sydney Olympic Park Authority — no answer
('lead:call:sopa-20260914-1','lead:acct:sydney-olympic-park-authority','2026-09-14T15:00:00','afternoon','ari','mobile','0461 260 180','Genna Kaur (Procurement)',
 'N','','','retry in a different time window; ask about vendor registration path','','',1,'2026-09-14T15:00:00');
