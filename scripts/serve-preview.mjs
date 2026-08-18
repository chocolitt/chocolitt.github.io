import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve, sep } from "node:path";

const host = "127.0.0.1";
const port = Number.parseInt(process.argv[2] ?? "4321", 10);
const distDirectory = resolve(import.meta.dirname, "../dist");

const contentTypes = new Map([
  [".css", "text/css; charset=utf-8"],
  [".gif", "image/gif"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".jpeg", "image/jpeg"],
  [".jpg", "image/jpeg"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".mp3", "audio/mpeg"],
  [".mp4", "video/mp4"],
  [".pdf", "application/pdf"],
  [".png", "image/png"],
  [".svg", "image/svg+xml"],
  [".txt", "text/plain; charset=utf-8"],
  [".webm", "video/webm"],
  [".webp", "image/webp"],
  [".woff", "font/woff"],
  [".woff2", "font/woff2"],
  [".xml", "application/xml; charset=utf-8"],
  [".zip", "application/zip"],
]);

function resolveRequestPath(requestUrl) {
  const pathname = decodeURIComponent(new URL(requestUrl, `http://${host}`).pathname);
  let relativePath = normalize(pathname).replace(/^[/\\]+/, "");

  if (relativePath === "" || pathname.endsWith("/")) {
    relativePath = join(relativePath, "index.html");
  }

  let candidate = resolve(distDirectory, relativePath);
  if (!candidate.startsWith(`${distDirectory}${sep}`) && candidate !== distDirectory) {
    return null;
  }

  if ((!existsSync(candidate) || statSync(candidate).isDirectory()) && extname(candidate) === "") {
    candidate = join(candidate, "index.html");
  }

  return candidate;
}

const server = createServer((request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.writeHead(405, { Allow: "GET, HEAD" });
    response.end();
    return;
  }

  let filePath;
  try {
    filePath = resolveRequestPath(request.url ?? "/");
  } catch {
    filePath = null;
  }

  if (!filePath || !existsSync(filePath) || !statSync(filePath).isFile()) {
    filePath = join(distDirectory, "404.html");
    response.statusCode = 404;
  }

  response.setHeader("Content-Type", contentTypes.get(extname(filePath).toLowerCase()) ?? "application/octet-stream");
  response.setHeader("Cache-Control", "no-store");

  if (request.method === "HEAD") {
    response.end();
    return;
  }

  createReadStream(filePath).pipe(response);
});

server.listen(port, host, () => {
  console.log(`Website preview is ready at http://${host}:${port}/`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => server.close(() => process.exit(0)));
}
