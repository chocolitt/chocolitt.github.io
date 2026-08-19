import pageTemplate from "../data/paper-reviews/page.html?raw";
import papersSource from "../data/paper-reviews/papers.json?raw";

export const prerender = true;

interface Badge {
  count: number;
  impact: string;
  serious: boolean;
}

interface Paper {
  id: string;
  code: string;
  title: string;
  summary: string;
  confidence: string;
  serious: boolean;
  badges: Badge[];
  disclosure?: string;
}

const papers = JSON.parse(papersSource) as Paper[];
const panelSources = import.meta.glob<string>("../data/paper-reviews/*/*.html", {
  eager: true,
  import: "default",
  query: "?raw",
});

function panelFor(paper: Paper, panel: "erratum" | "review" | "audit") {
  const source = panelSources[`../data/paper-reviews/${paper.id}/${panel}.html`];
  if (source === undefined) throw new Error(`Missing ${panel} source for ${paper.code}`);
  return source.trim();
}

function renderBadges(paper: Paper) {
  return paper.badges
    .map(
      (badge) =>
        `<span class="badge${badge.serious ? " serious" : ""}"><b>${badge.count}</b> ${badge.impact}</span>`,
    )
    .join("");
}

function renderPaper(paper: Paper) {
  return `
            <details class="paper card" id="${paper.id}" data-code="${paper.code}" data-serious="${paper.serious}">
              <summary>
                <span class="paper-code">${paper.code}</span>
                <span class="paper-title"><b>${paper.title}</b><small>${paper.summary}</small></span>
                <span class="paper-badges">${renderBadges(paper)}</span>
              </summary>
              <div class="paper-body">
                ${paper.disclosure ? `<p class="paper-disclosure">${paper.disclosure}</p>` : ""}
                <div class="paper-tools"><span>Audit confidence: ${paper.confidence}</span></div>
                <div class="tabs" role="tablist" aria-label="${paper.code} materials">
                  <button role="tab" aria-selected="true" data-tab="erratum">Erratum</button>
                  <button role="tab" aria-selected="false" data-tab="review">Refine review</button>
                  <button role="tab" aria-selected="false" data-tab="audit">Audit</button>
                </div>
                <section class="tab-panel prose erratum" data-panel="erratum" role="tabpanel">${panelFor(paper, "erratum")}</section>
                <section class="tab-panel prose" data-panel="review" role="tabpanel" hidden>${panelFor(paper, "review")}</section>
                <section class="tab-panel prose" data-panel="audit" role="tabpanel" hidden>${panelFor(paper, "audit")}</section>
              </div>
            </details>`;
}

function renderNavigation() {
  return [
    '<a href="#overall-audit"><span>Σ</span><b>Overall audit</b></a>',
    ...papers.map(
      (paper) =>
        `<a href="#${paper.id}" data-paper-link="${paper.id}"><span>${paper.code}</span><b>${paper.title}</b></a>`,
    ),
  ].join("\n");
}

function insert(source: string, marker: string, value: string) {
  if (!source.includes(marker)) throw new Error(`Missing paper-review page marker: ${marker}`);
  return source.replace(marker, () => value);
}

export function GET() {
  let page = insert(pageTemplate, "{{PAPER_NAVIGATION}}", renderNavigation());
  page = insert(page, "{{PAPER_COUNT}}", String(papers.length));
  page = insert(page, "{{PAPER_CARDS}}", papers.map(renderPaper).join("\n"));

  return new Response(page, {
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}
