export function canonicalPath(path: string): string {
  const suffixIndex = path.search(/[?#]/);
  const pathname = suffixIndex === -1 ? path : path.slice(0, suffixIndex);
  const suffix = suffixIndex === -1 ? "" : path.slice(suffixIndex);
  const lastSegment = pathname.split("/").at(-1) ?? "";

  if (pathname === "/" || pathname.endsWith("/") || lastSegment.includes(".")) return path;
  return `${pathname}/${suffix}`;
}
