import { processLatexToAstViaUnified } from "@unified-latex/unified-latex";

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function main() {
  try {
    const latex = await readStdin();

    const processor = processLatexToAstViaUnified();
    const file = await processor.process(latex);

    console.log(JSON.stringify(file.result));
  } catch (err) {
    console.error("ERROR:", err);
    process.exit(1);
  }
}

main();
