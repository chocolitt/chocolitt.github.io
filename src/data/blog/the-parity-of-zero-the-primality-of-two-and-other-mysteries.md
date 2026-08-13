---
title: "The parity of zero, the primality of two, and other mysteries"
description: "From time to time, I try to speak or write about mathematics for general (non-mathematical) audiences. If you've done this, you know it's pretty hard -- in large part because it's hard to know what people know, despite my best attempts t…"
published: "2017-07-19T16:01:00Z"
draft: false
tags: [{"name": "math", "path": "/blog/tag/math"}, {"name": "polls", "path": "/blog/tag/polls"}, {"name": "teaching", "path": "/blog/tag/teaching"}, {"name": "cool", "path": "/blog/tag/cool"}]
categories: [{"name": "math", "path": "/blog/category/math"}, {"name": "data", "path": "/blog/category/data"}]
comments: true
math: false
legacyPath: "/blog/2017/7/18/the-parity-of-zero-the-primality-of-two-and-other-mysteries"
imported: true
---

<p>From time to time, I try to speak or write about mathematics for general (non-mathematical) audiences.  If you've done this, you know it's pretty hard -- in large part because it's hard to know what people know, despite <a href="https://matheducators.stackexchange.com/questions/1869/adult-mathematical-literacy">my best attempts to find out</a>.</p><p>Enter <a href="https://surveys.google.com">Google Surveys</a>.  For a pretty reasonable fee, it turns out <em>anyone</em> can run a survey through Google; the respondents are randomly selected and reweighted by demographics (age, gender, location).  So I decided to find out:  What percentage of Americans over the age of 18 know what a <strong>prime number</strong> is?  What about an <strong>even number</strong>?  I also tried to design the questions so they tested a bit more than basic knowledge; for example, I wanted to know whether the respondents knew that zero is even (a <a href="http://www.bbc.com/news/magazine-20559052">surprisingly controversial topic</a>).</p><h2>Methodology</h2><p>Here are the two surveys I ran, as they would appear to respondents.  Each survey received about 250 responses from randomly selected Americans over the age of 18.  (And cost me a well-spent $25.)</p><p><strong>Even numbers:</strong></p>

<figure><img src="/assets/squarespace/6182dda74e39-image-asset.webp" alt="You&#x27;d think this one would be pretty easy..." loading="lazy" /><figcaption>You'd think this one would be pretty easy...</figcaption></figure>

<p>I included 0 because I suspected it would be the most "difficult" number to identify as even; I included 774 to check that people know how to deal with large-ish numbers.  17 and 99 were supposed to be easy, whereas 257 was aimed at checking if people were simply looking for an even digit.</p><p><strong>Prime numbers:</strong></p>

<figure><img src="/assets/squarespace/c45c4ce91738-image-asset.webp" alt="Maybe a little tougher." loading="lazy" /><figcaption>Maybe a little tougher.</figcaption></figure>

<p>Here 57 is included <a href="https://en.wikipedia.org/wiki/57_(number)">in honor of Grothendieck</a>.</p><p>The order of the answers was reversed for a random half of the respondents.  As I understand it, Google shows these questions on sites with some premium content -- users can take the survey in lieu of paying.</p><h2>Data</h2><p>You can download the raw data for the survey on even numbers <a href="/s/Even-Numbers.xls">here</a>, and the survey on prime numbers <a href="/s/Primes.xls">here</a>.  The data includes the type of website on which the survey was taken (news, arts and entertainment, reference, etc.), the gender of the respondent, their approximate age, region within the US, whether they are browsing from a rural, suburban, or urban area, their approximate income, and the amount of time it took them to respond to the question.  Google infers much of this data from the browsing habits of the user, though, so I don't know how reliable it is.</p><h2>Analysis</h2><p>So, what percentage of American know that 2 is a prime number?  That zero is even?</p>

<figure><img src="/assets/squarespace/01b6690ecf8c-image-asset.webp" alt="Well 8 is pretty even, I guess." loading="lazy" /><figcaption>Well 8 is pretty even, I guess.</figcaption></figure>

<p>The percentages indicate how many survey-takers thought the number in question was even.  So about 75.7% of people think 8 is even (not bad!) but 774 is much harder.  I don't know what was going on with the 0.8% of people who thought that 17 was even, but maybe this is an example of the <a href="http://slatestarcodex.com/2013/04/12/noisy-poll-results-and-reptilian-muslim-climatologists-from-mars/">Lizardman constant</a>.</p>

<figure><img src="/assets/squarespace/03c67e1fb25c-image-asset.webp" alt="Yeesh." loading="lazy" /><figcaption>Yeesh.</figcaption></figure>

<p>(Note that the histogram above says that there were 199 respondents.  In fact, there were 250, but because of the reweighing, the survey only had the power of the survey with 199 truly randomly-chosen respondents.)  The good news is that more than 40% of survey-takers knew that 13 is prime; on the other hand, 17% thought that 9 is prime.  That said, I founded it heartening that the top three answers were indeed the three primes.  That's the wisdom of crowds for you.</p><p>How did the respondents do overall?  Below are graphs indicating what percentage of respondents got 0,1, ..., 6 answers correct on each survey.</p><p><strong>Even numbers:</strong></p>

<figure><img src="/assets/squarespace/c85b7dfdc1e0-image-asset.webp" alt="Not bad!" loading="lazy" /><figcaption>Not bad!</figcaption></figure>

<p>In particular, more than half of the survey-takers were able to get 5 or 6 answers correct.  Not too shabby!  To get a perfect score, one had to identify zero as even, which only 24% of the respondents were able to do, so I think this is a pretty good result.  Interestingly, about 2/3 of the people who correctly identified zero as even got perfect scores.  The median number of correct answers was 5 out of 6; the mean was about 4.5.</p><p><strong>Prime numbers:</strong></p>

<figure><img src="/assets/squarespace/8480f517d71c-image-asset.webp" alt="Pretty tough." loading="lazy" /><figcaption>Pretty tough.</figcaption></figure>

<p>Identifying primes was evidently much harder.  The median number of correct answers was 3 out of 6 (no better than chance), and the mean was about 3.6.</p><p>I did do some more detailed analysis (e.g. breaking the results down by demographics, looking at the response time, etc.) but didn't find anything particularly interesting.  But for your edification, here is a plot of median response time (in milliseconds) against the number of correct answers to the survey on even numbers.</p>

<figure><img src="/assets/squarespace/715d5e815f5c-Screen-Shot-2017-07-18-at-10.35.10-PM.webp" alt="Hmm." loading="lazy" /><figcaption>Hmm.</figcaption></figure>

<p>There seems to be a weak relationship between time spent and the number of correct answers (though the people who answered almost everything wrong did so pretty slowly), but maybe this isn't surprising.</p><h2>Conclusions</h2><p>I actually found these results pretty heartening!  My biggest worry is that I'm now addicted to polls, at $25 a pop.</p><p>I was a bit surprised how few respondents knew that 0 is even.  Parity is a concept which actually comes up in daily life -- for example, when one wants to know which side of the street a given address is on, or in <a href="http://www.bbc.com/news/magazine-20559052">certain regulatory questions</a>.  I was also a bit surprised that it was so difficult to identify 2 as a prime.</p><p>Of course there are some problems with these polls.  The biggest, in my opinion, is that they don't let people indicate how sure they are -- one worry I have is that if people weren't sure if, say, 2 was prime, they'd just leave it blank.  So, for the sake of symmetry, I should really run another survey, asking people to identify <strong>non-prime</strong><strong> </strong>numbers.  I suspect far fewer than 70% of respondents would say 2 is composite.  If I decide to run another survey, I'll post about it here, of course.</p><p>Please let me know if you download and do anything with the data!  (<a href="/s/Even-Numbers.xls">Data on even numbers</a>, <a href="/s/Primes.xls">data on primes</a>.)</p><p> </p>
