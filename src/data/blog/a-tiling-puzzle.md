---
title: "A tiling puzzle"
description: "Here are four magic triominoes: [caption id=\"\" align=\"alignnone\" width=\"1216\"] Four magic triominoes [/caption] Each is made out of three squares, two red and one blue or two blue and one red, alternating in color. These squares have the…"
published: "2022-08-05T21:49:49Z"
draft: false
tags: []
categories: []
comments: true
math: false
legacyPath: "/blog/2022/8/5/a-tiling-puzzle"
imported: true
---

<p>Here are four magic triominoes: </p>

       <figure><img src="/assets/squarespace/c9383c7fcecf-IMG_0223.webp" alt="Four magic triominoes" loading="lazy" /><figcaption>Four magic triominoes</figcaption></figure>

  <p>Each is made out of three squares, two red and one blue or two blue and one red, alternating in color. These squares have the following property: if you place two squares of the same color on top of each other, they stack. On the other hand, if you place a red square on top of a blue square, they annihilate each other.</p><p>For example, if you place the following two triominoes, so that the rightmost square of the first aligns with the bottom square of the second, you get the following configuration:</p>

       <figure><img src="/assets/squarespace/33ef7e4a1d9c-IMG_0227.webp" alt="Placing two triominoes so that squares of opposite colors are on top of each other annihilates those squares." loading="lazy" /><figcaption>Placing two triominoes so that squares of opposite colors are on top of each other annihilates those squares.</figcaption></figure>

  <p>But if you place the same two triominoes so that the middle square of the first aligns with the bottom square of the second, those two red squares stack, which I’ve indicated by a two below (i.e. there is a stack of height two at that location):</p>

      <img src="/assets/squarespace/3e9246d170ba-IMG_0226.webp" alt="" loading="lazy" />

  <p>Your goal is: given an N x M chessboard of squares, place these triominoes onto the chessboard so that every square is covered by exactly one red tile. (Note that the tiles aren’t allowed to stick off the edge of the board.)</p><p>For which (N,M) is this possible (with proof)? Feel free to post solutions in comments; if no one posts a solution in a week or so I’ll update with a solution.</p>
