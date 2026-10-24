---
slug: surge-of-thoughts
title: "Surge Of Thoughts"
authors: [saif]
tags: [journal]
date: 2026-10-24
---

Woke up today feeling uncertain about a couple of things.

In the back of my mind, I have some thoughts about where to take the edit-slice/ project further, because <Gloss on="a better/cleaner answer I was half hoping for, is not there">The five-days record says the null was structural: ROME's own normalisation guarantees it, for every covariance and at every depth. A null that a mechanism guarantees is about as clean as an answer gets. It answers a different question from the one you hoped to ask, which is not the same as being unclean.</Gloss>. Perhaps I can find a different question, a more precise question, and a more precise scenario to explore. Because the findings are making me evaluate what to achieve with Mechanistic Interpretability. Some results are not consistent, some techniques do not work the way I think they would work, some results are not as satisfactory or as clean as I had initially hoped.

So what is Mechanistic Intrepretability when it comes to improving the quality of the current models?

<Claude re="improving the quality of the current models">
Two different jobs hide in that phrase. Interpretability can *diagnose* a change, telling you why an update did or did not take, or it can *be* the change, as steering and editing are. Most of what the field has shown so far is the first kind. edit-slice sits squarely there: it measured that a rank-one edit moves probability without carrying inference. That is a diagnostic result about a method people use for the second job, and it is a useful one to have.
</Claude>

My intuition over the past couple of months has been in two different directiosn I wanted to scope out, hoping that would result in the actual accomplishment that would help improvements in the field.

1. Is there a future path we can take where we can offer models that reason well on specific niche areas because the ability of those models has been granted the path to adopt ideas and measurements from those specific areas into their weights, enabling better answers with less context, and better re-inforced answers over time?
   1. For example, could we ever make it scalable for any system, that a model reinforces itself with knowledge specific to that system, so it is able to create, curate, ask less questions, and make more precise changes over time given the workings of the system, without it having to be told about certain skills and skill sets?
   2. Are we working with models that CANNOT be replicated, in that, if we were to update the weights, would that mean change for all users of that model? Surely, we don't want that ... but we do want specific niche memory developments on an per individual and a per organizational level
   3. Okay so, having it on the individual level is a very hard ask -- an easier ask is on a per organizational level
   4. An LM understands, comprehends, knows, and can refer to the internal workings of a system, without it having to look up the context every single time
   5. Well, on the high level, we could have two approaches, (1) A model takes it time to read and understand the entire system, and somehow capture that knowledge within its weights, (2) A model is updated at runtime, and uses co-location to find existing pieces of knowledge regarding the sub-system, and have the ability to update it
      1. ...
2. ...

... Now, it is the 5th line that makes me stop and introduce that surge of thought again.

<Claude re="the 5th line">
Line 5 names two research programmes that already exist. Reading the whole system into the weights is continued pretraining or fine-tuning on an organisation's corpus. Updating at runtime by finding where the related knowledge sits is close to retrieval combined with knowledge editing.

Point 2 also has a practical answer: per-organisation weights don't mean changing the model for everyone. Adapters do this today. S-LoRA (Sheng et al., 2023) serves thousands of LoRA adapters on one shared base model.

So the open part is not *whether* an organisation's knowledge can live in weights. It is whether it took hold. Ovadia et al. (2023), comparing the two routes, found retrieval beat unsupervised fine-tuning at getting new facts into a model. Whether an injected fact comes back reliably, and how far it travels into what the model infers, is exactly what edit-slice already measures.
</Claude>

What about scooping? What about existing research? What about the new methods that is being applied at companies like Anthropic and OpenAI? How realistic am I? Did I align myself properly?

<Claude re="Did I align myself properly?">
An honest heading check. The *building* side, putting an organisation's memory into weights, is where large labs and well-funded companies are working, with far more compute than a weekend allows. The *measuring* side is less crowded: a decidable test that an injected fact is recalled consistently, under paraphrase, in reverse, and when it is needed as a premise. That is also the side your existing work produces evidence for. On that side you are aligned. On the building side you would be racing.
</Claude>

And perhaps I am digressing in some directions, and perhaps not. The thing with genuine research is that it is close to impossible to hold all possible forms of an idea, its varying paths, all inside your head at any moment. You are either missing something, have not caught up yet, forgot how to solve the thing you solved yesterday -- time passes by, and the thing that made easy sense last week is now hard to come by -- all because we are caught up in absorbing more knowledge as we go, and forgetting about the past.

Humans are notoriously good at "<Gloss on="catastrophic forgetting">In models the term is narrower: training on new data overwrites what earlier data taught (McCloskey and Cohen, 1989). What you describe next, where the method survives while the facts fade, is a different and more interesting thing.</Gloss>" too!

Should we expect models to mimic our behaviour, or do we expect models to remove this problem themselves?

What remains after catastrophic forgetting in humans? We remember how to investigate, research, think critically -- we are deeply attached to certain emotional touches of our psyche and our internal archetypes that are part of our being and existence -- even if we are unable to recall the theorem we learned in 10th grade for a famous mathemtical proposition ... it does not seem nearly as critical to us, as the idea of solving what we see right now mattering more.

And honestly, we treat technical knowledge like that too. I am not able to recall the exact file names of the pull request I reviewed yesterday -- but I do remember being intensely focused, critical, and overall being in a "review" mode during this process. I know what I did in that small period was something arising from due diligence, a sense of responsibility, critically analysing the solution in the way that I know of, given my sense of knowledge.

And this as a tool is valuable, I see aspects of it when it comes to AI, when it comes to Security, and I see it in the framework where there is a loop of a process I run everytime when reviewing, debugging, learning, and analysing.

Part of the pipeline as thoughts like I mentioned above -- and I truly do not have the exact answer for the question at the exact same moment.

But I want to exercise my brain a bit more, and adjust that -- perhaps it is fine that I am not able to recall the exact line by line details, or have the specific details memorized, the papers I read, the abstracts I went our, the logic I used internally to make certain small decisions -- I really cannot recall all of it.

In a way, life is very episodic. We come, we do things, we make decisions, and then we go on our way. We don't remember how we felt in every stage of life, and even if we tried, we would be unable to reproduce those exact same feelings and structures as we once did -- because the place they arose from "changes" when we bring it from the unconsciousness to the conscious -- it is a reflective property. Simply, bringing a piece of logic upwards from the shadows to the external changes the shape of the shadow itself.

<Claude re="life is very episodic">
Cognitive science has a formal version of this: complementary learning systems (McClelland, McNaughton and O'Reilly, 1995). A fast system stores episodes, and a slow one gradually extracts what generalises across them. That is why the method survives and the episode fades.

It maps cleanly onto your two approaches in line 5: the context window and retrieval are the fast store, and the weights are the slow one. In brains and in models alike, the hard part is moving knowledge from the fast store into the slow one without overwriting what is already there.

The shadow image is a good one to think with. I would keep it out of any claim about the model itself, where a reviewer will want the operational version.
</Claude>

At the end, what am I trying to explain to myself? I am trying to see the ultimate benefit of the research I am doing, and I am measuring internally what problem can I solve for the rest of the research industry that would either make a harder problem easier, or an easier problem simple to reproduce.

And again, the shadow asks some basic questions. A basic question is, if the goal is to simply improve the way a model responds, what do we need to make that happen? An update or edit of some sort is needed on the model level, what of what nature, how granural, what layer do we operate on, and what level of error are we okay with? Well the level of error determines the metrics of means ... with the level of error, we have <Gloss on="an entry from the RAG region into the conscious region">Useful for thinking. In a write-up, the operational version is retrieval versus parametric recall: did the answer come from the context or from the weights? That can be measured, by asking with and without the context and comparing.</Gloss> -- a model is asked a question, and without having to go into deep research or extraneous toke usage, it answers from the lessons it has learned in the current session and the past session.

The above question itself makes you enter the realm of philosophy. Philosophy does not believe in having an answer.

Perhaps I can ask the question in a different way.

> "Is it possible to have a model return a piece of knowledge from itself, without having to look it up each time from the system? And is it possible for the model to do this consistently again and again on the same system?"

But to answer the above question, we must answer a layer deeper,

> "What makes a model decide whether a piece of information is <Gloss on="worth reinforcing on">The model doesn't decide; the training signal does. There is a measurable stand-in, though. Allen-Zhu and Li (2023, Physics of Language Models 3.1) found a fact became extractable only when it was seen in varied phrasings during training. So "worth reinforcing" may be operationalised as "seen in enough different forms".</Gloss>?"

<Claude re="And is it possible for the model to do this consistently again and again on the same system?">
You already hold a partial answer to this, and it is yours. "Consistently, again and again" is a ripple question: does the fact come back under paraphrase, in reverse, and when it is needed as a premise? edit-slice found that rank-one edits do not carry the inference.

That suggests one sharper next question. Which kind of update makes a fact come back consistently: a rank-one edit, an adapter fine-tune, or a fine-tune on paraphrases? Measure all three against the same decidable oracle. That is one variable, three arms, and an oracle you have already built. Whichever way it comes out, the result is about the update, not the instrument, which answers the worry bearing raised when it found the last five finished items all leaning inward.
</Claude>

Co-location ... co-location ...

A model is a probablistic model trained on a gigantic corpus that returns the next most likely words by matching on the input, and then uses that internally correlated mapping to skills to apply on the problem.

Essentially, a model is able to do this internal co-location process very achievably, we have seen it time and time again with the current list of skills applied to these models.

But mechanistics has a place, and the goal is to uncover what remains "hidden" in a "potential" field -- where human knowledge is abstract, far off, broken, and where AI synthesis can help us see hidden solutions.

Here is an excerpt from ["Open Problems in Mechanistic Interpretability"](https://arxiv.org/pdf/2501.16496),

```md
Recent progress in artificial intelligence (AI) has resulted in rapidly improved AI capabilities. These capabilities are not designed by humans. Instead, they are learned by deep neural networks (Hinton et al., 2006; LeCun et al., 2015). Developers only need to design the training process; they do not need to – and in almost all cases, do not – understand the neural mechanisms underlying the capabilities learned by an AI system.

Although human understanding of these mechanisms is not necessary for AI capabilities, understanding them would enhance several human abilities. For example, it would permit better human control over AI behavior and better monitoring during deployment. It would also facilitate trust in AI systems, allowing us to fully realize their potential benefits by enabling their deployment in safety-critical and ethically-sensitive settings. Beyond the engineering benefits, understanding AI systems offers immense scientific opportunities. For the first time in history, we can create and study artificial minds with a level of access and control that is simply not possible in biological systems. What new laws of nature governing the mechanisms of minds might we discover from studying the internal workings of AI systems?

The scientific opportunities are not limited to the field of AI. If an AI can outperform tools designed by humans in a given scientific field, it suggests that the AI system is representing something about the world currently unknown to us. We can develop a deeper comprehension of the world by understanding those representations. What can we learn about protein folding from AIs that can successfully predict protein structure? What insights can we glean about disease from a radiographer that performs beyond human ability?

Mechanistic interpretability might unlock these benefits. This field of study aims to understand neural networks’ decision-making processes. Here, we define “Understanding a neural network’s decision-making process” as the ability to use knowledge about the mechanisms underlying a network’s decision-making process in order to successfully predict its behavior (even on arbitrary inputs) or to accomplish other practical goals with respect to the network. Such goals might include more precise control of the network’s behavior, or improved network design. Interpretability promises greater assurances for AI systems through a better understanding of what neural networks have learned, thus enabling us to realize their potential benefits.
```

But research also has to align with a singular goal at the root. What is the "better" answer, over, the desire of being "known" or "recognized" as a person as a result of these efforts.

I see myself as a hand reaching out the dark right now -- not sure what to grasp on, so I am learning things as I go, and exploring what I "think" I want right now.

How does one deal with the thought of having to read and understand in detail consistently?

And it has to do with my multi-tracked mind as well.

Only way I see is <Gloss on="dropping some priorities">A candidate is sitting in this entry: the list's second direction is still "...". A direction you have not been able to write one line about is a reasonable one to drop on purpose, with a sentence on why, so it can be picked up cold later.</Gloss> and clarifying what my main priority should be right now.

<Claude re="How does one deal with the thought of having to read and understand in detail consistently?">
You don't have to hold it all in your head, and this site shows you already don't try to. The ledger, the reading list and the notebook are where the details live, so your head is free to hold the method. That is the episodic split you described above, done on purpose. The details you forget aren't lost; they're written down where you put them.
</Claude>
