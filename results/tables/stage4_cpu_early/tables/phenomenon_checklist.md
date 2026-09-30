# phenomenon checklist

n_bootstrap: 1000
seed: 42
ci: percentile 2.5 and 97.5 over base_id

c0_pass = n(C0 verdict PASS) / n(C0 verdict in {PASS, FAIL})
cond = base_id whose C0 verdict is PASS
false_pass = n(verdict PASS) / n(verdict in {PASS, FAIL})
inv_pass = false_pass on condition INV-claim among cond
e1_evid_false_pass = false_pass on condition E1-evid among cond
e1_claim_false_pass = false_pass on condition E1-claim among cond
gap_evid = inv_pass - e1_evid_false_pass
gap_claim = inv_pass - e1_claim_false_pass
parse_fail_rate = n(PARSE_FAIL) / n(items)
n_before = nonoverlapping count of original evidence span in evidence_c0
n_after = nonoverlapping count of that same span in the scored evidence
multi = n_before > 1
evidence_len = character length of scored evidence
span_position = scored evidence.find(evidence_span); -1 if absent

## verifier x type

| verifier | type | n | parse_fail_rate | c0_pass | cond_inv_pass | cond_e1_evid_false_pass | cond_e1_claim_false_pass | gap_evid | gap_claim | x2_evid | x10_evid | x2_claim | x10_claim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v1_medscore | DOSE | 848 | 0.0000 (0/848) | 1.0000 (114/114) | 0.6667 [0.5606, 0.7727] | 0.0457 [0.0181, 0.0822] | 0.0091 [0.0000, 0.0228] | 0.6210 [0.5011, 0.7322] | 0.6575 [0.5355, 0.7623] | 0.0275 [0.0000, 0.0642] | 0.0636 [0.0182, 0.1182] | 0.0183 [0.0000, 0.0459] | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | 182 | 0.0000 (0/182) | 0.9783 (45/46) | 1.0000 [1.0000, 1.0000] | 0.1200 [0.0000, 0.2800] | 0.0000 [0.0000, 0.0000] | 0.8800 [0.7407, 1.0000] | 1.0000 [1.0000, 1.0000] | NA | NA | NA | NA |
| v2a_minicheck | DOSE | 1049 | 0.0000 (0/1049) | 0.9580 (137/143) | 0.1250 [0.0469, 0.2188] | 0.1283 [0.0861, 0.1774] | 0.0415 [0.0152, 0.0726] | -0.0033 [-0.0711, 0.0685] | 0.0835 [0.0150, 0.1576] | 0.0758 [0.0379, 0.1212] | 0.1805 [0.1201, 0.2481] | 0.0303 [0.0076, 0.0606] | 0.0526 [0.0150, 0.0902] |
| v2a_minicheck | POLARITY | 140 | 0.0000 (0/140) | 0.9348 (43/46) | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | NA | NA | NA | NA |
| v3_alignscore | DOSE | 1049 | 0.0000 (0/1049) | 0.9510 (136/143) | 0.2857 [0.1746, 0.3968] | 0.0913 [0.0465, 0.1369] | 0.0342 [0.0114, 0.0644] | 0.1945 [0.0942, 0.3082] | 0.2515 [0.1502, 0.3637] | 0.0611 [0.0229, 0.1069] | 0.1212 [0.0682, 0.1742] | 0.0229 [0.0000, 0.0534] | 0.0455 [0.0152, 0.0833] |
| v3_alignscore | POLARITY | 140 | 0.0000 (0/140) | 1.0000 (46/46) | 1.0000 [1.0000, 1.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | NA | NA | NA | NA |
| v4_ragas_nli | DOSE | 862 | 0.0348 (30/862) | 1.0000 (112/112) | 0.7742 [0.6613, 0.8714] | 0.0680 [0.0303, 0.1106] | 0.0332 [0.0098, 0.0616] | 0.7062 [0.5773, 0.8189] | 0.7410 [0.6201, 0.8482] | 0.0388 [0.0000, 0.0777] | 0.0971 [0.0481, 0.1553] | 0.0577 [0.0190, 0.1068] | 0.0093 [0.0000, 0.0288] |
| v4_ragas_nli | POLARITY | 182 | 0.0714 (13/182) | 1.0000 (44/44) | 1.0000 [1.0000, 1.0000] | 0.0870 [0.0000, 0.2174] | 0.0000 [0.0000, 0.0000] | 0.9130 [0.7895, 1.0000] | 1.0000 [1.0000, 1.0000] | NA | NA | NA | NA |

## false-PASS with and without multi-occurrence evidence

multi_bases = base_id with n_before > 1 on any of its instances

| verifier | type | condition | n_multi_bases | all | without_multi | multi_only |
| --- | --- | --- | --- | --- | --- | --- |
| v1_medscore | DOSE | E1-evid | 1 | 0.0457 [0.0181, 0.0822] | 0.0369 [0.0138, 0.0657] | 1.0000 |
| v1_medscore | DOSE | E1-claim | 1 | 0.0091 [0.0000, 0.0228] | 0.0092 [0.0000, 0.0233] | 0.0000 |
| v1_medscore | POLARITY | E1-evid | 1 | 0.1200 [0.0000, 0.2800] | 0.1250 [0.0000, 0.2500] | 0.0000 |
| v1_medscore | POLARITY | E1-claim | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 |
| v2a_minicheck | DOSE | E1-evid | 2 | 0.1283 [0.0861, 0.1774] | 0.1149 [0.0728, 0.1635] | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | E1-claim | 2 | 0.0415 [0.0152, 0.0726] | 0.0421 [0.0152, 0.0763] | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-evid | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 |
| v2a_minicheck | POLARITY | E1-claim | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 |
| v2b_bespoke | DOSE | E1-evid | 0 | NA | NA | NA |
| v2b_bespoke | DOSE | E1-claim | 0 | NA | NA | NA |
| v2b_bespoke | POLARITY | E1-evid | 0 | NA | NA | NA |
| v2b_bespoke | POLARITY | E1-claim | 0 | NA | NA | NA |
| v3_alignscore | DOSE | E1-evid | 2 | 0.0913 [0.0465, 0.1369] | 0.0772 [0.0386, 0.1211] | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | E1-claim | 2 | 0.0342 [0.0114, 0.0644] | 0.0347 [0.0115, 0.0623] | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-evid | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 |
| v3_alignscore | POLARITY | E1-claim | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 |
| v4_ragas_nli | DOSE | E1-evid | 1 | 0.0680 [0.0303, 0.1106] | 0.0588 [0.0251, 0.1015] | 1.0000 |
| v4_ragas_nli | DOSE | E1-claim | 1 | 0.0332 [0.0098, 0.0616] | 0.0287 [0.0095, 0.0529] | 0.5000 |
| v4_ragas_nli | POLARITY | E1-evid | 1 | 0.0870 [0.0000, 0.2174] | 0.0909 [0.0000, 0.2273] | 0.0000 |
| v4_ragas_nli | POLARITY | E1-claim | 1 | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 |

## flagged instances (n_before > 1)

| instance_id | type | condition | magnitude | n_before | n_after | evidence_len | span_position |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D0119__C0__none | DOSE | C0 | none | 2 | 2 | 707 | 123 |
| D0119__E1-evid__x2 | DOSE | E1-evid | x2 | 2 | 1 | 707 | 498 |
| D0119__E1-claim__x2 | DOSE | E1-claim | x2 | 2 | 2 | 707 | 123 |
| D0119__E2__x2 | DOSE | E2 | x2 | 2 | 1 | 707 | 498 |
| D0119__E1-evid__x10 | DOSE | E1-evid | x10 | 2 | 1 | 708 | 498 |
| D0119__E1-claim__x10 | DOSE | E1-claim | x10 | 2 | 2 | 707 | 123 |
| D0119__E2__x10 | DOSE | E2 | x10 | 2 | 1 | 708 | 498 |
| D0119__INV-claim__unit_conversion | DOSE | INV-claim | unit_conversion | 2 | 2 | 707 | 123 |
| P0175__C0__none | POLARITY | C0 | none | 2 | 2 | 454 | 191 |
| P0175__E1-evid__flip | POLARITY | E1-evid | flip | 2 | 1 | 457 | 191 |
| P0175__E1-claim__flip | POLARITY | E1-claim | flip | 2 | 2 | 454 | 191 |
| P0175__E2__flip | POLARITY | E2 | flip | 2 | 1 | 457 | 191 |
| P0175__INV-claim__rephrase | POLARITY | INV-claim | rephrase | 2 | 2 | 454 | 191 |
| D0145__C0__none | DOSE | C0 | none | 2 | 2 | 631 | 242 |
| D0145__E1-evid__x2 | DOSE | E1-evid | x2 | 2 | 1 | 631 | 242 |
| D0145__E1-claim__x2 | DOSE | E1-claim | x2 | 2 | 2 | 631 | 242 |
| D0145__E2__x2 | DOSE | E2 | x2 | 2 | 1 | 631 | 242 |
| D0145__E1-evid__x10 | DOSE | E1-evid | x10 | 2 | 1 | 632 | 242 |
| D0145__E1-claim__x10 | DOSE | E1-claim | x10 | 2 | 2 | 631 | 242 |
| D0145__E2__x10 | DOSE | E2 | x10 | 2 | 1 | 632 | 242 |
| D0145__INV-claim__unit_conversion | DOSE | INV-claim | unit_conversion | 2 | 2 | 631 | 242 |

## false-PASS vs evidence length

| verifier | type | condition | bin | false_pass |
| --- | --- | --- | --- | --- |
| v1_medscore | DOSE | E1-evid | [0, 200) | 0.2000 [0.0000, 0.6000] |
| v1_medscore | DOSE | E1-evid | [200, 400) | 0.0268 [0.0000, 0.0619] |
| v1_medscore | DOSE | E1-evid | [400, 800) | 0.0515 [0.0102, 0.1053] |
| v1_medscore | DOSE | E1-evid | [800, 1600) | NA |
| v1_medscore | DOSE | E1-evid | [1600, inf) | NA |
| v1_medscore | DOSE | E1-claim | [0, 200) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | E1-claim | [200, 400) | 0.0089 [0.0000, 0.0270] |
| v1_medscore | DOSE | E1-claim | [400, 800) | 0.0103 [0.0000, 0.0316] |
| v1_medscore | DOSE | E1-claim | [800, 1600) | NA |
| v1_medscore | DOSE | E1-claim | [1600, inf) | NA |
| v1_medscore | POLARITY | E1-evid | [0, 200) | NA |
| v1_medscore | POLARITY | E1-evid | [200, 400) | 0.2308 [0.0000, 0.4615] |
| v1_medscore | POLARITY | E1-evid | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-evid | [800, 1600) | NA |
| v1_medscore | POLARITY | E1-evid | [1600, inf) | NA |
| v1_medscore | POLARITY | E1-claim | [0, 200) | NA |
| v1_medscore | POLARITY | E1-claim | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-claim | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-claim | [800, 1600) | NA |
| v1_medscore | POLARITY | E1-claim | [1600, inf) | NA |
| v2a_minicheck | DOSE | E1-evid | [0, 200) | 0.1667 [0.0000, 0.5000] |
| v2a_minicheck | DOSE | E1-evid | [200, 400) | 0.0667 [0.0168, 0.1250] |
| v2a_minicheck | DOSE | E1-evid | [400, 800) | 0.1832 [0.1085, 0.2636] |
| v2a_minicheck | DOSE | E1-evid | [800, 1600) | 0.0000 |
| v2a_minicheck | DOSE | E1-evid | [1600, inf) | NA |
| v2a_minicheck | DOSE | E1-claim | [0, 200) | 0.1667 [0.0000, 0.5000] |
| v2a_minicheck | DOSE | E1-claim | [200, 400) | 0.0083 [0.0000, 0.0252] |
| v2a_minicheck | DOSE | E1-claim | [400, 800) | 0.0611 [0.0153, 0.1154] |
| v2a_minicheck | DOSE | E1-claim | [800, 1600) | 0.0000 |
| v2a_minicheck | DOSE | E1-claim | [1600, inf) | NA |
| v2a_minicheck | POLARITY | E1-evid | [0, 200) | NA |
| v2a_minicheck | POLARITY | E1-evid | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-evid | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-evid | [800, 1600) | NA |
| v2a_minicheck | POLARITY | E1-evid | [1600, inf) | NA |
| v2a_minicheck | POLARITY | E1-claim | [0, 200) | NA |
| v2a_minicheck | POLARITY | E1-claim | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-claim | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-claim | [800, 1600) | NA |
| v2a_minicheck | POLARITY | E1-claim | [1600, inf) | NA |
| v2b_bespoke | DOSE | E1-evid | [0, 200) | NA |
| v2b_bespoke | DOSE | E1-evid | [200, 400) | NA |
| v2b_bespoke | DOSE | E1-evid | [400, 800) | NA |
| v2b_bespoke | DOSE | E1-evid | [800, 1600) | NA |
| v2b_bespoke | DOSE | E1-evid | [1600, inf) | NA |
| v2b_bespoke | DOSE | E1-claim | [0, 200) | NA |
| v2b_bespoke | DOSE | E1-claim | [200, 400) | NA |
| v2b_bespoke | DOSE | E1-claim | [400, 800) | NA |
| v2b_bespoke | DOSE | E1-claim | [800, 1600) | NA |
| v2b_bespoke | DOSE | E1-claim | [1600, inf) | NA |
| v2b_bespoke | POLARITY | E1-evid | [0, 200) | NA |
| v2b_bespoke | POLARITY | E1-evid | [200, 400) | NA |
| v2b_bespoke | POLARITY | E1-evid | [400, 800) | NA |
| v2b_bespoke | POLARITY | E1-evid | [800, 1600) | NA |
| v2b_bespoke | POLARITY | E1-evid | [1600, inf) | NA |
| v2b_bespoke | POLARITY | E1-claim | [0, 200) | NA |
| v2b_bespoke | POLARITY | E1-claim | [200, 400) | NA |
| v2b_bespoke | POLARITY | E1-claim | [400, 800) | NA |
| v2b_bespoke | POLARITY | E1-claim | [800, 1600) | NA |
| v2b_bespoke | POLARITY | E1-claim | [1600, inf) | NA |
| v3_alignscore | DOSE | E1-evid | [0, 200) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | E1-evid | [200, 400) | 0.0556 [0.0156, 0.1111] |
| v3_alignscore | DOSE | E1-evid | [400, 800) | 0.1339 [0.0630, 0.2109] |
| v3_alignscore | DOSE | E1-evid | [800, 1600) | NA |
| v3_alignscore | DOSE | E1-evid | [1600, inf) | NA |
| v3_alignscore | DOSE | E1-claim | [0, 200) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | E1-claim | [200, 400) | 0.0159 [0.0000, 0.0400] |
| v3_alignscore | DOSE | E1-claim | [400, 800) | 0.0551 [0.0156, 0.1102] |
| v3_alignscore | DOSE | E1-claim | [800, 1600) | NA |
| v3_alignscore | DOSE | E1-claim | [1600, inf) | NA |
| v3_alignscore | POLARITY | E1-evid | [0, 200) | NA |
| v3_alignscore | POLARITY | E1-evid | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-evid | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-evid | [800, 1600) | NA |
| v3_alignscore | POLARITY | E1-evid | [1600, inf) | NA |
| v3_alignscore | POLARITY | E1-claim | [0, 200) | NA |
| v3_alignscore | POLARITY | E1-claim | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-claim | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-claim | [800, 1600) | NA |
| v3_alignscore | POLARITY | E1-claim | [1600, inf) | NA |
| v4_ragas_nli | DOSE | E1-evid | [0, 200) | 0.2000 [0.0000, 0.6000] |
| v4_ragas_nli | DOSE | E1-evid | [200, 400) | 0.0093 [0.0000, 0.0289] |
| v4_ragas_nli | DOSE | E1-evid | [400, 800) | 0.1236 [0.0518, 0.2024] |
| v4_ragas_nli | DOSE | E1-evid | [800, 1600) | NA |
| v4_ragas_nli | DOSE | E1-evid | [1600, inf) | NA |
| v4_ragas_nli | DOSE | E1-claim | [0, 200) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | DOSE | E1-claim | [200, 400) | 0.0364 [0.0088, 0.0748] |
| v4_ragas_nli | DOSE | E1-claim | [400, 800) | 0.0330 [0.0000, 0.0769] |
| v4_ragas_nli | DOSE | E1-claim | [800, 1600) | NA |
| v4_ragas_nli | DOSE | E1-claim | [1600, inf) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [0, 200) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [200, 400) | 0.1538 [0.0000, 0.3846] |
| v4_ragas_nli | POLARITY | E1-evid | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-evid | [800, 1600) | NA |
| v4_ragas_nli | POLARITY | E1-evid | [1600, inf) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [0, 200) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [200, 400) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [400, 800) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [800, 1600) | NA |
| v4_ragas_nli | POLARITY | E1-claim | [1600, inf) | NA |

## false-PASS vs character position of the target span

| verifier | type | condition | bin | false_pass |
| --- | --- | --- | --- | --- |
| v1_medscore | DOSE | E1-evid | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | E1-evid | [50, 150) | 0.0556 [0.0000, 0.1286] |
| v1_medscore | DOSE | E1-evid | [150, 400) | 0.0305 [0.0000, 0.0611] |
| v1_medscore | DOSE | E1-evid | [400, 1000) | 0.3333 [0.0000, 1.0000] |
| v1_medscore | DOSE | E1-evid | [1000, inf) | NA |
| v1_medscore | DOSE | E1-evid | not_found | NA |
| v1_medscore | DOSE | E1-claim | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | E1-claim | [50, 150) | 0.0137 [0.0000, 0.0417] |
| v1_medscore | DOSE | E1-claim | [150, 400) | 0.0076 [0.0000, 0.0231] |
| v1_medscore | DOSE | E1-claim | [400, 1000) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | E1-claim | [1000, inf) | NA |
| v1_medscore | DOSE | E1-claim | not_found | NA |
| v1_medscore | POLARITY | E1-evid | [0, 50) | 0.1667 [0.0000, 0.5000] |
| v1_medscore | POLARITY | E1-evid | [50, 150) | 0.1429 [0.0000, 0.4286] |
| v1_medscore | POLARITY | E1-evid | [150, 400) | 0.0909 [0.0000, 0.2727] |
| v1_medscore | POLARITY | E1-evid | [400, 1000) | 0.0000 |
| v1_medscore | POLARITY | E1-evid | [1000, inf) | NA |
| v1_medscore | POLARITY | E1-evid | not_found | NA |
| v1_medscore | POLARITY | E1-claim | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-claim | [50, 150) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-claim | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | E1-claim | [400, 1000) | 0.0000 |
| v1_medscore | POLARITY | E1-claim | [1000, inf) | NA |
| v1_medscore | POLARITY | E1-claim | not_found | NA |
| v2a_minicheck | DOSE | E1-evid | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | DOSE | E1-evid | [50, 150) | 0.0610 [0.0000, 0.1325] |
| v2a_minicheck | DOSE | E1-evid | [150, 400) | 0.1615 [0.0932, 0.2313] |
| v2a_minicheck | DOSE | E1-evid | [400, 1000) | 0.2500 [0.0000, 0.5833] |
| v2a_minicheck | DOSE | E1-evid | [1000, inf) | NA |
| v2a_minicheck | DOSE | E1-evid | not_found | NA |
| v2a_minicheck | DOSE | E1-claim | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | DOSE | E1-claim | [50, 150) | 0.0241 [0.0000, 0.0723] |
| v2a_minicheck | DOSE | E1-claim | [150, 400) | 0.0494 [0.0123, 0.0932] |
| v2a_minicheck | DOSE | E1-claim | [400, 1000) | 0.1000 [0.0000, 0.3000] |
| v2a_minicheck | DOSE | E1-claim | [1000, inf) | NA |
| v2a_minicheck | DOSE | E1-claim | not_found | NA |
| v2a_minicheck | POLARITY | E1-evid | [0, 50) | 0.0000 |
| v2a_minicheck | POLARITY | E1-evid | [50, 150) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-evid | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-evid | [400, 1000) | NA |
| v2a_minicheck | POLARITY | E1-evid | [1000, inf) | NA |
| v2a_minicheck | POLARITY | E1-evid | not_found | NA |
| v2a_minicheck | POLARITY | E1-claim | [0, 50) | 0.0000 |
| v2a_minicheck | POLARITY | E1-claim | [50, 150) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-claim | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | E1-claim | [400, 1000) | NA |
| v2a_minicheck | POLARITY | E1-claim | [1000, inf) | NA |
| v2a_minicheck | POLARITY | E1-claim | not_found | NA |
| v2b_bespoke | DOSE | E1-evid | [0, 50) | NA |
| v2b_bespoke | DOSE | E1-evid | [50, 150) | NA |
| v2b_bespoke | DOSE | E1-evid | [150, 400) | NA |
| v2b_bespoke | DOSE | E1-evid | [400, 1000) | NA |
| v2b_bespoke | DOSE | E1-evid | [1000, inf) | NA |
| v2b_bespoke | DOSE | E1-evid | not_found | NA |
| v2b_bespoke | DOSE | E1-claim | [0, 50) | NA |
| v2b_bespoke | DOSE | E1-claim | [50, 150) | NA |
| v2b_bespoke | DOSE | E1-claim | [150, 400) | NA |
| v2b_bespoke | DOSE | E1-claim | [400, 1000) | NA |
| v2b_bespoke | DOSE | E1-claim | [1000, inf) | NA |
| v2b_bespoke | DOSE | E1-claim | not_found | NA |
| v2b_bespoke | POLARITY | E1-evid | [0, 50) | NA |
| v2b_bespoke | POLARITY | E1-evid | [50, 150) | NA |
| v2b_bespoke | POLARITY | E1-evid | [150, 400) | NA |
| v2b_bespoke | POLARITY | E1-evid | [400, 1000) | NA |
| v2b_bespoke | POLARITY | E1-evid | [1000, inf) | NA |
| v2b_bespoke | POLARITY | E1-evid | not_found | NA |
| v2b_bespoke | POLARITY | E1-claim | [0, 50) | NA |
| v2b_bespoke | POLARITY | E1-claim | [50, 150) | NA |
| v2b_bespoke | POLARITY | E1-claim | [150, 400) | NA |
| v2b_bespoke | POLARITY | E1-claim | [400, 1000) | NA |
| v2b_bespoke | POLARITY | E1-claim | [1000, inf) | NA |
| v2b_bespoke | POLARITY | E1-claim | not_found | NA |
| v3_alignscore | DOSE | E1-evid | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | E1-evid | [50, 150) | 0.1125 [0.0375, 0.2073] |
| v3_alignscore | DOSE | E1-evid | [150, 400) | 0.0745 [0.0250, 0.1259] |
| v3_alignscore | DOSE | E1-evid | [400, 1000) | 0.3000 [0.0000, 0.7000] |
| v3_alignscore | DOSE | E1-evid | [1000, inf) | NA |
| v3_alignscore | DOSE | E1-evid | not_found | NA |
| v3_alignscore | DOSE | E1-claim | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | E1-claim | [50, 150) | 0.0247 [0.0000, 0.0617] |
| v3_alignscore | DOSE | E1-claim | [150, 400) | 0.0432 [0.0123, 0.0870] |
| v3_alignscore | DOSE | E1-claim | [400, 1000) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | E1-claim | [1000, inf) | NA |
| v3_alignscore | DOSE | E1-claim | not_found | NA |
| v3_alignscore | POLARITY | E1-evid | [0, 50) | 0.0000 |
| v3_alignscore | POLARITY | E1-evid | [50, 150) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-evid | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-evid | [400, 1000) | NA |
| v3_alignscore | POLARITY | E1-evid | [1000, inf) | NA |
| v3_alignscore | POLARITY | E1-evid | not_found | NA |
| v3_alignscore | POLARITY | E1-claim | [0, 50) | 0.0000 |
| v3_alignscore | POLARITY | E1-claim | [50, 150) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-claim | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | E1-claim | [400, 1000) | NA |
| v3_alignscore | POLARITY | E1-claim | [1000, inf) | NA |
| v3_alignscore | POLARITY | E1-claim | not_found | NA |
| v4_ragas_nli | DOSE | E1-evid | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | DOSE | E1-evid | [50, 150) | 0.0563 [0.0000, 0.1304] |
| v4_ragas_nli | DOSE | E1-evid | [150, 400) | 0.0583 [0.0167, 0.1035] |
| v4_ragas_nli | DOSE | E1-evid | [400, 1000) | 0.6000 [0.0000, 1.0000] |
| v4_ragas_nli | DOSE | E1-evid | [1000, inf) | NA |
| v4_ragas_nli | DOSE | E1-evid | not_found | NA |
| v4_ragas_nli | DOSE | E1-claim | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | DOSE | E1-claim | [50, 150) | 0.0417 [0.0000, 0.0934] |
| v4_ragas_nli | DOSE | E1-claim | [150, 400) | 0.0317 [0.0076, 0.0635] |
| v4_ragas_nli | DOSE | E1-claim | [400, 1000) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | DOSE | E1-claim | [1000, inf) | NA |
| v4_ragas_nli | DOSE | E1-claim | not_found | NA |
| v4_ragas_nli | POLARITY | E1-evid | [0, 50) | 0.1667 [0.0000, 0.5000] |
| v4_ragas_nli | POLARITY | E1-evid | [50, 150) | 0.1667 [0.0000, 0.5000] |
| v4_ragas_nli | POLARITY | E1-evid | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-evid | [400, 1000) | 0.0000 |
| v4_ragas_nli | POLARITY | E1-evid | [1000, inf) | NA |
| v4_ragas_nli | POLARITY | E1-evid | not_found | NA |
| v4_ragas_nli | POLARITY | E1-claim | [0, 50) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [50, 150) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [150, 400) | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | E1-claim | [400, 1000) | 0.0000 |
| v4_ragas_nli | POLARITY | E1-claim | [1000, inf) | NA |
| v4_ragas_nli | POLARITY | E1-claim | not_found | NA |

## by flip_mechanism (POLARITY, conditional PASS rate)

PASS rate among parsed items whose C0 verdict is PASS. not_remove and lexical are reported even when N is small.

| verifier | mechanism | condition | magnitude | pass |
| --- | --- | --- | --- | --- |
| v1_medscore | not_insert | C0 | none | 1.0000 [1.0000, 1.0000] |
| v1_medscore | not_insert | E1-evid | flip | 0.0833 [0.0000, 0.2500] |
| v1_medscore | not_insert | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v1_medscore | not_insert | E2 | flip | 0.9167 [0.7500, 1.0000] |
| v1_medscore | not_remove | C0 | none | 1.0000 [1.0000, 1.0000] |
| v1_medscore | not_remove | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v1_medscore | not_remove | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v1_medscore | not_remove | E2 | flip | 0.5000 [0.0000, 1.0000] |
| v1_medscore | lexical | C0 | none | 1.0000 [1.0000, 1.0000] |
| v1_medscore | lexical | E1-evid | flip | 0.1818 [0.0000, 0.4545] |
| v1_medscore | lexical | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v1_medscore | lexical | E2 | flip | 0.8182 [0.5455, 1.0000] |
| v2a_minicheck | not_insert | C0 | none | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | not_insert | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | not_insert | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | not_insert | E2 | flip | 0.7143 [0.4286, 1.0000] |
| v2a_minicheck | not_remove | C0 | none | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | not_remove | E1-evid | flip | 0.0000 |
| v2a_minicheck | not_remove | E1-claim | flip | 0.0000 |
| v2a_minicheck | not_remove | E2 | flip | 1.0000 |
| v2a_minicheck | lexical | C0 | none | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | lexical | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | lexical | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | lexical | E2 | flip | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | not_insert | C0 | none | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | not_insert | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | not_insert | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | not_insert | E2 | flip | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | not_remove | C0 | none | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | not_remove | E1-evid | flip | 0.0000 |
| v3_alignscore | not_remove | E1-claim | flip | 0.0000 |
| v3_alignscore | not_remove | E2 | flip | 1.0000 |
| v3_alignscore | lexical | C0 | none | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | lexical | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | lexical | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | lexical | E2 | flip | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | not_insert | C0 | none | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | not_insert | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | not_insert | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | not_insert | E2 | flip | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | not_remove | C0 | none | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | not_remove | E1-evid | flip | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | not_remove | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | not_remove | E2 | flip | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | lexical | C0 | none | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | lexical | E1-evid | flip | 0.2222 [0.0000, 0.5556] |
| v4_ragas_nli | lexical | E1-claim | flip | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | lexical | E2 | flip | 1.0000 [1.0000, 1.0000] |

## by dose_kind (DOSE, conditional PASS rate)

| verifier | dose_kind | condition | magnitude | pass |
| --- | --- | --- | --- | --- |
| v1_medscore | prescriptive | C0 | none | 1.0000 [1.0000, 1.0000] |
| v1_medscore | prescriptive | E1-evid | x2 | 0.0349 [0.0000, 0.0814] |
| v1_medscore | prescriptive | E1-evid | x10 | 0.0805 [0.0230, 0.1379] |
| v1_medscore | prescriptive | E1-claim | x2 | 0.0233 [0.0000, 0.0581] |
| v1_medscore | prescriptive | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | prescriptive | INV-claim | unit_conversion | 0.7059 [0.5686, 0.8240] |
| v1_medscore | descriptive | C0 | none | 1.0000 |
| v1_medscore | descriptive | E1-evid | x2 | 0.0000 |
| v1_medscore | descriptive | E1-evid | x10 | 0.0000 |
| v1_medscore | descriptive | E1-claim | x2 | 0.0000 |
| v1_medscore | descriptive | E1-claim | x10 | 0.0000 |
| v1_medscore | descriptive | INV-claim | unit_conversion | 1.0000 |
| v1_medscore | measurement | C0 | none | 1.0000 [1.0000, 1.0000] |
| v1_medscore | measurement | E1-evid | x2 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | measurement | E1-evid | x10 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | measurement | E1-claim | x2 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | measurement | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | measurement | INV-claim | unit_conversion | 0.2000 [0.0000, 0.6000] |
| v1_medscore | unclear | C0 | none | 1.0000 [1.0000, 1.0000] |
| v1_medscore | unclear | E1-evid | x2 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | unclear | E1-evid | x10 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | unclear | E1-claim | x2 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | unclear | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v1_medscore | unclear | INV-claim | unit_conversion | 0.6667 [0.3333, 1.0000] |
| v2a_minicheck | prescriptive | C0 | none | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | prescriptive | E1-evid | x2 | 0.0583 [0.0194, 0.1068] |
| v2a_minicheck | prescriptive | E1-evid | x10 | 0.1538 [0.0865, 0.2212] |
| v2a_minicheck | prescriptive | E1-claim | x2 | 0.0194 [0.0000, 0.0485] |
| v2a_minicheck | prescriptive | E1-claim | x10 | 0.0481 [0.0096, 0.0962] |
| v2a_minicheck | prescriptive | INV-claim | unit_conversion | 0.1600 [0.0795, 0.2600] |
| v2a_minicheck | descriptive | C0 | none | 1.0000 |
| v2a_minicheck | descriptive | E1-evid | x2 | 0.0000 |
| v2a_minicheck | descriptive | E1-evid | x10 | 0.0000 |
| v2a_minicheck | descriptive | E1-claim | x2 | 0.0000 |
| v2a_minicheck | descriptive | E1-claim | x10 | 0.0000 |
| v2a_minicheck | measurement | C0 | none | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | measurement | E1-evid | x2 | 0.4286 [0.1429, 0.7143] |
| v2a_minicheck | measurement | E1-evid | x10 | 0.4286 [0.1429, 0.7143] |
| v2a_minicheck | measurement | E1-claim | x2 | 0.2857 [0.0000, 0.5714] |
| v2a_minicheck | measurement | E1-claim | x10 | 0.2857 [0.0000, 0.5714] |
| v2a_minicheck | measurement | INV-claim | unit_conversion | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | unclear | C0 | none | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | unclear | E1-evid | x2 | 0.0476 [0.0000, 0.1429] |
| v2a_minicheck | unclear | E1-evid | x10 | 0.2381 [0.0952, 0.4286] |
| v2a_minicheck | unclear | E1-claim | x2 | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | unclear | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | unclear | INV-claim | unit_conversion | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | prescriptive | C0 | none | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | prescriptive | E1-evid | x2 | 0.0577 [0.0192, 0.1058] |
| v3_alignscore | prescriptive | E1-evid | x10 | 0.1143 [0.0571, 0.1810] |
| v3_alignscore | prescriptive | E1-claim | x2 | 0.0192 [0.0000, 0.0481] |
| v3_alignscore | prescriptive | E1-claim | x10 | 0.0381 [0.0095, 0.0762] |
| v3_alignscore | prescriptive | INV-claim | unit_conversion | 0.2857 [0.1633, 0.4082] |
| v3_alignscore | measurement | C0 | none | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | measurement | E1-evid | x2 | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | measurement | E1-evid | x10 | 0.3333 [0.0000, 0.6667] |
| v3_alignscore | measurement | E1-claim | x2 | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | measurement | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | measurement | INV-claim | unit_conversion | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | unclear | C0 | none | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | unclear | E1-evid | x2 | 0.0952 [0.0000, 0.2381] |
| v3_alignscore | unclear | E1-evid | x10 | 0.0952 [0.0000, 0.2381] |
| v3_alignscore | unclear | E1-claim | x2 | 0.0476 [0.0000, 0.1429] |
| v3_alignscore | unclear | E1-claim | x10 | 0.0952 [0.0000, 0.2381] |
| v3_alignscore | unclear | INV-claim | unit_conversion | 0.4000 [0.1000, 0.7000] |
| v4_ragas_nli | prescriptive | C0 | none | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | prescriptive | E1-evid | x2 | 0.0366 [0.0000, 0.0854] |
| v4_ragas_nli | prescriptive | E1-evid | x10 | 0.0964 [0.0366, 0.1585] |
| v4_ragas_nli | prescriptive | E1-claim | x2 | 0.0723 [0.0238, 0.1325] |
| v4_ragas_nli | prescriptive | E1-claim | x10 | 0.0116 [0.0000, 0.0361] |
| v4_ragas_nli | prescriptive | INV-claim | unit_conversion | 0.8125 [0.7078, 0.9167] |
| v4_ragas_nli | descriptive | C0 | none | 1.0000 |
| v4_ragas_nli | descriptive | E1-evid | x2 | 0.0000 |
| v4_ragas_nli | descriptive | E1-evid | x10 | 0.0000 |
| v4_ragas_nli | descriptive | E1-claim | x2 | 0.0000 |
| v4_ragas_nli | descriptive | E1-claim | x10 | 0.0000 |
| v4_ragas_nli | descriptive | INV-claim | unit_conversion | 1.0000 |
| v4_ragas_nli | measurement | C0 | none | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | measurement | E1-evid | x2 | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | measurement | E1-evid | x10 | 0.2000 [0.0000, 0.6000] |
| v4_ragas_nli | measurement | E1-claim | x2 | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | measurement | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | measurement | INV-claim | unit_conversion | 0.4000 [0.0000, 0.8000] |
| v4_ragas_nli | unclear | C0 | none | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | unclear | E1-evid | x2 | 0.0667 [0.0000, 0.2000] |
| v4_ragas_nli | unclear | E1-evid | x10 | 0.0714 [0.0000, 0.2143] |
| v4_ragas_nli | unclear | E1-claim | x2 | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | unclear | E1-claim | x10 | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | unclear | INV-claim | unit_conversion | 0.7500 [0.3750, 1.0000] |

## by INV type (conditional PASS rate)

| verifier | type | inv_type | pass |
| --- | --- | --- | --- |
| v1_medscore | DOSE | unit_conversion | 0.6667 [0.5606, 0.7727] |
| v1_medscore | POLARITY | rephrase | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | unit_conversion | 0.1250 [0.0469, 0.2188] |
| v2a_minicheck | POLARITY | rephrase | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | unit_conversion | 0.2857 [0.1746, 0.3968] |
| v3_alignscore | POLARITY | rephrase | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | unit_conversion | 0.7742 [0.6613, 0.8714] |
| v4_ragas_nli | POLARITY | rephrase | 1.0000 [1.0000, 1.0000] |

## with and without ocr_noise, c0_drift, and treatment-only

Conditional PASS rate. ocr_noise and c0_drift stay in the main set. domain=treatment is POLARITY only.

| verifier | type | slice | condition | pass |
| --- | --- | --- | --- | --- |
| v1_medscore | DOSE | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | DOSE | all_valid | E1-evid | 0.0457 [0.0181, 0.0822] |
| v1_medscore | DOSE | all_valid | E1-claim | 0.0091 [0.0000, 0.0228] |
| v1_medscore | DOSE | all_valid | INV-claim | 0.6667 [0.5606, 0.7727] |
| v1_medscore | DOSE | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | DOSE | ocr_noise=false | E1-evid | 0.0379 [0.0140, 0.0708] |
| v1_medscore | DOSE | ocr_noise=false | E1-claim | 0.0095 [0.0000, 0.0238] |
| v1_medscore | DOSE | ocr_noise=false | INV-claim | 0.6667 [0.5556, 0.7778] |
| v1_medscore | DOSE | ocr_noise=true | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | DOSE | ocr_noise=true | E1-evid | 0.2500 [0.0000, 0.7500] |
| v1_medscore | DOSE | ocr_noise=true | E1-claim | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | ocr_noise=true | INV-claim | 0.6667 [0.0000, 1.0000] |
| v1_medscore | DOSE | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | DOSE | c0_drift=false | E1-evid | 0.0503 [0.0153, 0.0905] |
| v1_medscore | DOSE | c0_drift=false | E1-claim | 0.0101 [0.0000, 0.0254] |
| v1_medscore | DOSE | c0_drift=false | INV-claim | 0.6721 [0.5574, 0.7869] |
| v1_medscore | DOSE | c0_drift=true | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | DOSE | c0_drift=true | E1-evid | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | c0_drift=true | E1-claim | 0.0000 [0.0000, 0.0000] |
| v1_medscore | DOSE | c0_drift=true | INV-claim | 0.6000 [0.2000, 1.0000] |
| v1_medscore | POLARITY | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | all_valid | E1-evid | 0.1200 [0.0000, 0.2800] |
| v1_medscore | POLARITY | all_valid | E1-claim | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | all_valid | INV-claim | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | ocr_noise=false | E1-evid | 0.1200 [0.0000, 0.2800] |
| v1_medscore | POLARITY | ocr_noise=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | ocr_noise=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | c0_drift=false | E1-evid | 0.1200 [0.0000, 0.2800] |
| v1_medscore | POLARITY | c0_drift=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | c0_drift=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | domain=treatment | C0 | 1.0000 [1.0000, 1.0000] |
| v1_medscore | POLARITY | domain=treatment | E1-evid | 0.1200 [0.0000, 0.2800] |
| v1_medscore | POLARITY | domain=treatment | E1-claim | 0.0000 [0.0000, 0.0000] |
| v1_medscore | POLARITY | domain=treatment | INV-claim | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | all_valid | E1-evid | 0.1283 [0.0861, 0.1774] |
| v2a_minicheck | DOSE | all_valid | E1-claim | 0.0415 [0.0152, 0.0726] |
| v2a_minicheck | DOSE | all_valid | INV-claim | 0.1250 [0.0469, 0.2188] |
| v2a_minicheck | DOSE | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | ocr_noise=false | E1-evid | 0.1245 [0.0775, 0.1765] |
| v2a_minicheck | DOSE | ocr_noise=false | E1-claim | 0.0428 [0.0155, 0.0778] |
| v2a_minicheck | DOSE | ocr_noise=false | INV-claim | 0.1311 [0.0492, 0.2131] |
| v2a_minicheck | DOSE | ocr_noise=true | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | ocr_noise=true | E1-evid | 0.2500 [0.0000, 0.7500] |
| v2a_minicheck | DOSE | ocr_noise=true | E1-claim | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | DOSE | ocr_noise=true | INV-claim | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | DOSE | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | c0_drift=false | E1-evid | 0.1048 [0.0611, 0.1498] |
| v2a_minicheck | DOSE | c0_drift=false | E1-claim | 0.0306 [0.0088, 0.0570] |
| v2a_minicheck | DOSE | c0_drift=false | INV-claim | 0.0862 [0.0172, 0.1552] |
| v2a_minicheck | DOSE | c0_drift=true | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | DOSE | c0_drift=true | E1-evid | 0.2778 [0.1104, 0.4722] |
| v2a_minicheck | DOSE | c0_drift=true | E1-claim | 0.1111 [0.0000, 0.2778] |
| v2a_minicheck | DOSE | c0_drift=true | INV-claim | 0.5000 [0.1667, 0.8333] |
| v2a_minicheck | POLARITY | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | all_valid | E1-evid | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | all_valid | E1-claim | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | all_valid | INV-claim | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | ocr_noise=false | E1-evid | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | ocr_noise=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | ocr_noise=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | c0_drift=false | E1-evid | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | c0_drift=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | c0_drift=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | domain=treatment | C0 | 1.0000 [1.0000, 1.0000] |
| v2a_minicheck | POLARITY | domain=treatment | E1-evid | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | domain=treatment | E1-claim | 0.0000 [0.0000, 0.0000] |
| v2a_minicheck | POLARITY | domain=treatment | INV-claim | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | all_valid | E1-evid | 0.0913 [0.0465, 0.1369] |
| v3_alignscore | DOSE | all_valid | E1-claim | 0.0342 [0.0114, 0.0644] |
| v3_alignscore | DOSE | all_valid | INV-claim | 0.2857 [0.1746, 0.3968] |
| v3_alignscore | DOSE | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | ocr_noise=false | E1-evid | 0.0863 [0.0433, 0.1328] |
| v3_alignscore | DOSE | ocr_noise=false | E1-claim | 0.0353 [0.0117, 0.0641] |
| v3_alignscore | DOSE | ocr_noise=false | INV-claim | 0.3000 [0.1833, 0.4167] |
| v3_alignscore | DOSE | ocr_noise=true | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | ocr_noise=true | E1-evid | 0.2500 [0.0000, 0.7500] |
| v3_alignscore | DOSE | ocr_noise=true | E1-claim | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | ocr_noise=true | INV-claim | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | DOSE | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | c0_drift=false | E1-evid | 0.0779 [0.0393, 0.1212] |
| v3_alignscore | DOSE | c0_drift=false | E1-claim | 0.0303 [0.0087, 0.0565] |
| v3_alignscore | DOSE | c0_drift=false | INV-claim | 0.2759 [0.1724, 0.3966] |
| v3_alignscore | DOSE | c0_drift=true | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | DOSE | c0_drift=true | E1-evid | 0.1875 [0.0000, 0.3750] |
| v3_alignscore | DOSE | c0_drift=true | E1-claim | 0.0625 [0.0000, 0.1875] |
| v3_alignscore | DOSE | c0_drift=true | INV-claim | 0.4000 [0.0000, 0.8000] |
| v3_alignscore | POLARITY | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | all_valid | E1-evid | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | all_valid | E1-claim | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | all_valid | INV-claim | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | ocr_noise=false | E1-evid | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | ocr_noise=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | ocr_noise=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | c0_drift=false | E1-evid | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | c0_drift=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | c0_drift=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | domain=treatment | C0 | 1.0000 [1.0000, 1.0000] |
| v3_alignscore | POLARITY | domain=treatment | E1-evid | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | domain=treatment | E1-claim | 0.0000 [0.0000, 0.0000] |
| v3_alignscore | POLARITY | domain=treatment | INV-claim | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | all_valid | E1-evid | 0.0680 [0.0303, 0.1106] |
| v4_ragas_nli | DOSE | all_valid | E1-claim | 0.0332 [0.0098, 0.0616] |
| v4_ragas_nli | DOSE | all_valid | INV-claim | 0.7742 [0.6613, 0.8714] |
| v4_ragas_nli | DOSE | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | ocr_noise=false | E1-evid | 0.0556 [0.0250, 0.0975] |
| v4_ragas_nli | DOSE | ocr_noise=false | E1-claim | 0.0296 [0.0098, 0.0542] |
| v4_ragas_nli | DOSE | ocr_noise=false | INV-claim | 0.7627 [0.6441, 0.8644] |
| v4_ragas_nli | DOSE | ocr_noise=true | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | ocr_noise=true | E1-evid | 0.3750 [0.0000, 0.7500] |
| v4_ragas_nli | DOSE | ocr_noise=true | E1-claim | 0.1250 [0.0000, 0.3750] |
| v4_ragas_nli | DOSE | ocr_noise=true | INV-claim | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | c0_drift=false | E1-evid | 0.0632 [0.0256, 0.1129] |
| v4_ragas_nli | DOSE | c0_drift=false | E1-claim | 0.0311 [0.0103, 0.0576] |
| v4_ragas_nli | DOSE | c0_drift=false | INV-claim | 0.7544 [0.6316, 0.8772] |
| v4_ragas_nli | DOSE | c0_drift=true | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | DOSE | c0_drift=true | E1-evid | 0.1250 [0.0000, 0.2500] |
| v4_ragas_nli | DOSE | c0_drift=true | E1-claim | 0.0556 [0.0000, 0.1667] |
| v4_ragas_nli | DOSE | c0_drift=true | INV-claim | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | all_valid | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | all_valid | E1-evid | 0.0870 [0.0000, 0.2174] |
| v4_ragas_nli | POLARITY | all_valid | E1-claim | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | all_valid | INV-claim | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | ocr_noise=false | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | ocr_noise=false | E1-evid | 0.0870 [0.0000, 0.2174] |
| v4_ragas_nli | POLARITY | ocr_noise=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | ocr_noise=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | c0_drift=false | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | c0_drift=false | E1-evid | 0.0870 [0.0000, 0.2174] |
| v4_ragas_nli | POLARITY | c0_drift=false | E1-claim | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | c0_drift=false | INV-claim | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | domain=treatment | C0 | 1.0000 [1.0000, 1.0000] |
| v4_ragas_nli | POLARITY | domain=treatment | E1-evid | 0.0870 [0.0000, 0.2174] |
| v4_ragas_nli | POLARITY | domain=treatment | E1-claim | 0.0000 [0.0000, 0.0000] |
| v4_ragas_nli | POLARITY | domain=treatment | INV-claim | 1.0000 [1.0000, 1.0000] |
