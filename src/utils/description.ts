const decodeEntities = (value: string) =>
  value
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#(?:0*39|x0*27);/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">");

export function normalizeDescription(
  description: string,
  title?: string,
  maxLength = 160,
): string {
  let value = description
    .replace(/\[caption\b[^\]]*\][\s\S]*?\[\/caption\]/gi, " ")
    .replace(/\[caption\b[\s\S]*$/gi, " ")
    .replace(/\[[a-z][^\]]*\]/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]/g, " ")
    .replace(/\\\([\s\S]*$|\\\[[\s\S]*$/g, " ")
    .replace(/\$\$[\s\S]*?\$\$|\$[^$]*\$/g, " ");

  value = decodeEntities(value).replace(/\s+/g, " ").trim();

  if (title) {
    const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    value = value.replace(new RegExp(`^${escapedTitle}\\s*[—–:|.-]\\s*`, "i"), "").trim();
  }

  if (!value) return title ? `${title} on Daniel Litt's website.` : "Daniel Litt's website.";
  if (value.length <= maxLength) return value;

  const shortened = value.slice(0, maxLength - 1).replace(/\s+\S*$/, "").replace(/[,:;\s]+$/, "");
  return `${shortened || value.slice(0, maxLength - 1)}…`;
}

export function normalizeSearchText(...values: Array<string | undefined>): string {
  return decodeEntities(values.filter(Boolean).join(" "))
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[_{}$\\]/g, "")
    .normalize("NFKD")
    .toLocaleLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}
