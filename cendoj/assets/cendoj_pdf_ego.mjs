// Descarga de PDFs del CENDOJ con Ego Lite (el captcha lo resuelve la persona).
// Uso: pega tus pares [nombre, data-link], corre con:
// ego-browser nodejs -e "await import('file:///G:/RUTA/cendoj_pdf_ego.mjs')"
// Reglas: un TaskSpace por objetivo, pausas de 2 a 5 s, verificar %PDF,
// ante captcha llamar a task.handOff() y frenar (nunca reintentar en loop).
const docs = [
  ["01_ejemplo", "https://www.poderjudicial.es/search/AN/openDocument/HASH/OPTIMIZE"],
];
const SPACE_NAME = "cendoj-pdfs";
const OUT_DIR = "G:/SALIDA/pdfs";
const task = await taskSpace(SPACE_NAME);
const page = task.page("p1");
for (const [name, url] of docs) {
  try {
    await page.goto(url, { timeout: 60000 });
    await page.waitForSelector("css:object", { timeout: 15000 });
    const pdfRel = await page.evaluate(() => {
      const o = document.querySelector("object");
      return o ? (o.getAttribute("data") || "") : "";
    });
    if (!pdfRel) {
      console.log(JSON.stringify({ name, ok: false, error: "sin-object-posible-captcha" }));
      await task.handOff();
      break;
    }
    const dest = OUT_DIR + "/" + name + ".pdf";
    const res = await page.fetch(pdfRel, { saveAs: dest, timeout: 60000 });
    console.log(JSON.stringify({ name, ok: res.ok, status: res.status, dest }));
  } catch (e) {
    console.log(JSON.stringify({ name, ok: false, error: String(e).slice(0, 200) }));
  }
  await page.waitForTimeout(2000 + Math.random() * 3000);
}
// Al terminar: await task.finish({ keep: [] });
