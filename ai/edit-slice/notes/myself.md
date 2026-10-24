Hi Natalie, Arnab! Hope you are doing well.

I wanted to follow-up with some experiments from my side since our last conversation. During this September and Octoober, I had been travelling with family, so this investigation took some time. But I had some findings that I wanted to share.

For context, in our last call, we were talking about probing, propagation, what kind of facts do we expect to be updated, the nature of the different types of questions -- for example, geographical, temporal, historically connected, and such -- and is it possible to reach with some experiments to see how far an edit for information like this would propagate?

I thought a lot about it, and my mental model pictured a kind of a digram, such as a node, that is connected to some past nodes, and goes outwards to other nodes. If factual information is based on rationality, a cause and effect cycle, then taking a fact about a certain iconic piece's location and editing it to exist in a different location invokes indirection questions about possible change in the connected pieces of data. In this way, I pictured that history is this series of node events from the past to the future, and in between, if we modify a node's fact, it changes its history forwards, and in some cases, it also changes it backwards.


So that was the picture I started with, and I wanted to find a way to actually measure it rather than keep arguing with myself about it. The problem I kept running into is that to measure how far an edit travels, you need to already agree on what counts as "related" -- and every benchmark I looked at answers that with some form of semantic distance, which is a judgement call wearing a number. I wanted something that could not be argued with.

What I ended up doing was going back to ROME's own arithmetic, which I had been treating as a black box until then. ROME's update divides by one quantity, u·k*, and k* is the key it computes at the subject token. So I asked a simple question: if my test prompt happens to begin with the same subject I edited, what is the key at that token? Under causal attention it is the same vector. Identical. Which means the coefficient is not approximately one, it is exactly one -- for any covariance, at every layer, no matter what the question is actually asking about. That is not something I fitted, it falls out of the formula.

I measured it to make sure I had not fooled myself, and it came out at 1.000 across four models from 6B up to 405B. Then I built a floor by taking the same prompts and scoring them against a completely different edit -- someone else's subject entirely -- and that sits at 0.082. The two distributions do not overlap anywhere across 23,505 readings.

This is where the picture I had started with came apart, and honestly it took me a while to accept it.

I went and looked at RippleEdits, which has a test type meant to check exactly the thing we were discussing -- whether an edit propagates outward to a different entity that you reach *through* the edited one. One of their prompts reads: "the name of the head of government of the place of death of Leo Arons is". And Leo Arons -- the subject I edited -- is sitting right there inside the prompt. So the update does not travel outward through any chain of related facts. It arrives directly, by arithmetic, because the string is present. I measured a median of 0.982 across their prompts of that type, against a floor of 0.070 on those same prompts.

What that means is that an editing method could score well on that test without generalising at all. The test cannot tell apart the two cases it was built to tell apart.

I want to be careful about what I am claiming here, because there is a limit I found and I would rather state it myself than have it pointed out to me. All of this is about *delivery* -- what fraction of the update arrives at a token. It is not about effect. When I hold the coefficient fixed at exactly 1.000, how far the edit actually reaches still varies by a factor of 2.96, and the best account I have of that variation explains about 28.5% of it. So none of this says the answer changed. It says the measurement cannot distinguish what it claims to distinguish.

The part that stopped this from being just a complaint about a benchmark is MQuAKE. I checked whether it has the same problem and it does not -- it names the edited subject if and only if the edit sits on the first hop of the chain, 6,861 out of 6,861 on one side and 0 out of 16,506 on the other. A clean split. So benchmarks that avoid this already exist in the field's own data, seemingly by construction rather than by design. And since the coefficient comes from a single forward pass through the *unedited* model, you can check any test item for this before running a single edit. That is the small instrument this all turned into, and it is really the only thing I would want to defend.

The closest published work I have found is ChainEdit (arXiv 2507.08427). They find a different problem in the same benchmark -- their questions require external knowledge the model may not hold -- and their repaired versions do not remove the edited subject from the prompt. One of them actually adds more context. So a benchmark fixed for their problem would still fail this check.

What I would most value from each of you is different.

Natalie -- is a cheap pre-run criterion for whether a propagation item can actually test propagation something the field would use? Or is it a restatement of what benchmark authors already do by eye? I genuinely cannot answer that from inside this, and it decides whether this is a paper or just a note I keep for myself.

Arnab -- I would rather you broke this than agreed with it. If there is one objection that kills it, I want that one rather than a list. I have written up my own attack surface and the nine claims I have already had to withdraw, so if the fatal objection is already in there and I have under-weighted it, telling me which one would be the most useful thing.

The write-up is here: https://rubix982.github.io/open-concept-lab/notebook/edit-slice/review -- section 7 opens with this screen and section 6 is where I try to attack it myself. Twenty minutes if you read only those two.

Thank you both, and apologies again for the long gap.

Saif
