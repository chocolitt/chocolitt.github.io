---
title: "The End of Mathematics"
description: "I'm currently returning to Toronto from a summit on the future of mathematics, at OpenAI. Sebastian Bubeck asked me to talk a bit about the future we'd all like to avoid, where humans are mathematically disempowered. Jacob Tsimerman advi…"
published: "2026-08-11T22:49:34Z"
draft: false
tags: []
categories: []
comments: true
math: false
legacyPath: "/blog/2026/8/11/the-end-of-mathematics"
imported: true
---

<p>I'm currently returning to Toronto from a summit on the future of mathematics, at OpenAI. Sebastian Bubeck asked me to talk a bit about the future we'd all like to avoid, where humans are mathematically disempowered. Jacob Tsimerman advised us to try to prioritize detail over correctness, and I have no doubt that I succeeded in deprioritizing correctness.</p>
<p>I tried to find a title that wasn't too bombastic:</p>
<p><img src="/images/blog/end-of-mathematics/01-title-slide.jpg" alt="The End of Mathematics title slide" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>The premise of the workshop (which we took as a starting point, rather than subject to debate, for the sake of productive discussion) was that AI will become robustly superhuman at mathematics. I want to tell a story in which, despite this, mathematical progress stalls. To be clear this is not a prediction--I'm optimistic by nature and think we'll find a way to adapt--but I am trying to imagine what a future in which certain existing trends continue might look like.</p>
<p><img src="/images/blog/end-of-mathematics/02-premise.jpg" alt="Premise of the talk" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<h2>2026</h2>
<p>What's clear is that we are at the start of a massive explosion of mathematical outputs; for example, below is the number of combinatorics papers posted per week to arXiv since late 2021. Other areas show a similar, but not quite dramatic, rise. I imagine a time series of tweets about math results would look similar.</p>
<p><img src="/images/blog/end-of-mathematics/03-output-growth.jpg" alt="Growth in mathematical outputs" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>What's less clear is how interesting or correct this surplus is, let alone how much of it is being meaningfully engaged with. Nonetheless it contains a number of striking and significant new results.</p>
<p><img src="/images/blog/end-of-mathematics/04-significant-results.jpg" alt="Examples of significant new results" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>At the same time certain organs of the mathematical community are atrophying. Below is a graph of MathOverflow questions and answers by month; these numbers have been in slow decline for some time as MathOverflow's function has been cannibalized by Discord etc., but the decline since the beginning of 2025 is likely due in large part to AI. What I find striking here is that there are both fewer questions <em>and fewer answers</em>. For example, I was not able to find an increase in answers to older questions in the statistics here, or really any other statistic I could spin as positive.</p>
<p><img src="/images/blog/end-of-mathematics/05-mathoverflow.jpg" alt="MathOverflow questions and answers by month" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>Even among the most interesting results produced by AI, something odd is starting to happen. For example, three groups independently produced very similar proofs of Feige's 1/e conjecture almost simultaneously; two groups disclosed that the result was found by AI. After <a href="https://x.com/__alpoge__">@__alpoge__</a> posted Fable's counterexample to the Jacobian conjecture in dimension \geq 3, an internal model at OAI replicated it; likewise Anthropic replicated many of the recent results OpenAI has announced. The models, and the people using them, seem to be solving the same problems.</p>
<p><img src="/images/blog/end-of-mathematics/06-duplicated-results.jpg" alt="Different groups and models duplicating mathematical results" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>In practice this means that a huge amount of duplicative labor, both in flesh and in silico, is being devoted to work whose marginal value to mathematics is, essentially, the cost of the tokens and perhaps a few bits of information indicating that the problem can be solved by existing models.</p>
<p><img src="/images/blog/end-of-mathematics/07-duplicative-labor.jpg" alt="Duplicative labor" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<h2>2027</h2>
<p>Of course this work might have value to the people announcing it (credit, PR, etc.).</p>
<p>Right now we try to incentivize the production of high quality science by rewarding people who produce papers, prove theorems and resolve conjectures, etc. But these outputs are now mispriced, and incentivizing them is not obviously optimal for the production of high quality science. What happens if we continue to do so in the next years?</p>
<p>I think if we do, the dominant strategy for career success (at least in the medium term) is playing the slot machine for conjectures. In fact one does not even have to choose the conjectures--you can just ask codex to pick them and resolve them and check the work. If you care about producing correct papers you can produce multiple short papers per day this way (and people who are doing so); if you don't care about correctness you can produce far more (and people are doing this too).</p>
<p>What's the value-add? The cost of the tokens? Certainly not the expertise developed--there is none. No one, not even the author, is reading much of this work. Mathematicians are no longer connected to the underlying mathematics. Even human verification is arguably less valuable as the models become more reliable.</p>
<p><img src="/images/blog/end-of-mathematics/08-profession-2027.jpg" alt="The mathematical profession in 2027" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>Moreover this has seriously negative effects on the math community. We are near the point where the models can reconstruct a paper given a few key ideas. Some of the autonomous AI results we are starting to see have a "last mile" flavor, where they finish off a problem after deep recent work by others. In this world talking about one's work in progress--or even indicating that the models can solve a given problem--is increasingly dangerous (at least if we still reward such work with prestige, jobs, etc.).</p>
<p>I've recently been told by multiple colleagues that they are unwilling to discuss work in progress for this reason.</p>
<p><img src="/images/blog/end-of-mathematics/09-work-in-progress.jpg" alt="Risks of discussing work in progress" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<h2>2028</h2>
<p>Nonetheless there are some bright spots. Autoformalization becomes cheap and effective. Many gaps or errors in the literature are discovered and repaired.</p>
<p>Much hay has been made of the necessity of human judgment here, to check that statements and definitions are formalized correctly. I am skeptical of this--I see no reason the models will not be able to do this effectively.</p>
<p>On the other hand, we are already starting to see cases (e.g. the two examples in the slide below) where formalizations differ from the English text they are formalizing in ways that may not be obvious to the readers. Again mathematicians are becoming disconnected from mathematics--while they might be able to trust the <em>statements</em> in past work, it is harder to trust the <em>ideas</em>. Informalization helps with this a bit but it is costly and time-consuming.</p>
<p><img src="/images/blog/end-of-mathematics/10-autoformalization.jpg" alt="Autoformalization in 2028" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<h2>2029-</h2>
<p>Despite this, the profession still incentivizes the production of papers. Models start to fulfill all the functions human mathematicians do now: theory-building, conjecturing, resolving conjectures, iterating, etc. Human mathematicians are doing "lab science" with agents, perhaps directing compute to questions they find interesting.</p>
<p>Who is engaging with this work? How are we training the next generation? It's not clear to me that our current institutions, if they do not adapt to this new regime, continue to produce high-quality mathematicians. Indeed it seems to me that our existing incentive structures will start to reward people who <em>do not</em> engage deeply with the mathematics, or, arguably, care about it at all.</p>
<p><img src="/images/blog/end-of-mathematics/11-profession-2029.jpg" alt="The mathematical profession from 2029 onward" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>Will this lead to a sustainable mathematical practice? I think plausibly not. Why would such people continue to devote resources to agents doing mathematics at all? Perhaps this is what the long term of mathematics research looks like, in this world:</p>
<p><img src="/images/blog/end-of-mathematics/12-long-term-future.jpg" alt="A possible long-term future for mathematical research" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>A summary of some possible risks:</p>
<p><img src="/images/blog/end-of-mathematics/13-risk-summary.jpg" alt="A summary of possible risks" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>I want to point out that these problems are reflections of the fact that the profession itself is already imperfect in various ways. This isn't surprising--as AI-induced change puts stress on our institutions, they will of course crack in the places where they are already flawed. Perhaps this exogenous shock will give us a chance to fix some of these flaws.</p>
<p><img src="/images/blog/end-of-mathematics/14-existing-flaws.jpg" alt="Existing flaws in the mathematical profession" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>Our institutions have certain values (production of high quality science, human capital, human understanding, etc.) that we try to achieve by rewarding people who contribute to them, with fun, prestige, etc. These values persist in a world with highly capable AI, but the mechanisms we use to achieve them are in many cases not robust to highly capable AI.</p>
<p><img src="/images/blog/end-of-mathematics/15-values-and-incentives.jpg" alt="Institutional values and incentives" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>Some final questions:</p>
<p><img src="/images/blog/end-of-mathematics/16-final-questions.jpg" alt="Final questions" width="1600" height="900" loading="lazy" class="imported-media media-slide" /></p>
<p>For what it's worth, I'm broadly optimistic that mathematics will survive and flourish. We have the opportunity to learn and understand incredible things. I think we'll adapt.</p>
<p>I think many of these concerns may seem quaint or parochial in the next few years, as highly capable models cause massive social upheaval beyond the world of abstract mathematics. My hope is that the questions I raise here are narrow enough to be considered productively, though, and that our answers might serve as a model for others as they too are impacted.</p>
